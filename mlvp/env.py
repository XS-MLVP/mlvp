from .logger import error, warning
from .model import Model
from .asynchronous import gather, create_task
from .agent import Monitor, Driver

class MsgScheduler:
    """The message scheduler."""

    def __init__(self, env, queue: list, models: list):
        self.env = env
        self.queue = queue
        self.models = models

    async def schedule(self):
        """
        Message execution in the queue is scheduled and forwarded to the model.

        Returns:
            The results of all schedule groups.
        """

        raise NotImplementedError("The method sche is not implemented")

    @staticmethod
    async def sequential_execution_all(*tasks):
        """Sequentially execute all tasks."""

        results = []
        for task in tasks:
            results.append(await task)
        return results

class ModelFirstScheduler(MsgScheduler):
    """
    The model first message scheduler. Before actually driving the DUT, the scheduler forwards the message to all the
    reference models in order.
    """

    async def __get_model_results(self):
        """
        Get the results from the models.
        It will add the results to the drive queue with the key "model_results".
        """

        for item in self.queue:
            driver: Driver = item["driver"]

            results = await driver.forward_to_models(self.models, item["args"], item["kwargs"])
            item["model_results"] = results

    async def __wrapped_coro(self, coro, queue_item):
        """
        Wrap the coro so that it can compare with the model results after the DUT is driven.
        """

        queue_item["dut_result"] = await coro

        driver = queue_item["driver"]
        if driver.need_compare:
            driver.compare_results(queue_item["dut_result"], queue_item["model_results"])

    async def __get_dut_results(self):
        """
        Get the results from the DUT and compare them with the model results.
        """

        # Group all tasks by sche_group
        all_tasks = {}
        for item in self.queue:
            func = item["driver"].func
            sche_group = item["sche_group"]

            if sche_group not in all_tasks:
                all_tasks[sche_group] = []

            all_tasks[sche_group].append(self.__wrapped_coro(func(self.env, *item["args"], **item["kwargs"]), item))

        # Generate all tasks to be executed
        sche_groups = []
        for sche_group, tasks in all_tasks.items():
            if len(tasks) == 1:
                sche_groups.append(tasks[0])
            else:
                sche_groups.append(self.sequential_execution_all(*tasks))

        # Execute all tasks
        await gather(*sche_groups)

    async def schedule(self):
        await self.__get_model_results()
        await self.__get_dut_results()

        results = {}
        for item in self.queue:
            if item["sche_group"] not in results:
                results[item["sche_group"]] = []
            results[item["sche_group"]].append(item["dut_result"])

        for key in results:
            if len(results[key]) == 1:
                results[key] = results[key][0]

        return results

class BeforeModelScheduler(MsgScheduler):
    """
    The Before model message scheduler.

    Msg will be executed before it is sent to the Model. Specifically, when an Msg is executed, it is immediately
    forwarded to all models.
    """

    async def forward_to_models(self, queue_item):
        """
        Forward the item to the models and add the results to queue_item.
        """

        driver: Driver = queue_item["driver"]
        results = await driver.forward_to_models(self.models, queue_item["args"], queue_item["kwargs"])
        queue_item["model_results"] = results

    async def wrapped_coro(self, coro, queue_item):
        """
        Wrap the coro so that it can forward the item to the models before it is executed. After both the model and the
        DUT are driven, the results will be compared.
        """

        queue_item["dut_result"] = await coro
        await self.forward_to_models(queue_item)

        driver = queue_item["driver"]
        if driver.need_compare:
            driver.compare_results(queue_item["dut_result"], queue_item["model_results"])

    async def __get_results(self):
        """
        Get the results from the DUT and the models.
        """

        # Group all tasks by sche_group
        all_tasks = {}
        for item in self.queue:
            func = item["driver"].func
            sche_group = item["sche_group"]

            if sche_group not in all_tasks:
                all_tasks[sche_group] = []

            all_tasks[sche_group].append(self.wrapped_coro(func(self.env, *item["args"], **item["kwargs"]), item))

        # Generate all tasks to be executed
        sche_groups = []
        for sche_group, tasks in all_tasks.items():
            if len(tasks) == 1:
                sche_groups.append(tasks[0])
            else:
                sche_groups.append(self.sequential_execution_all(*tasks))

        # Execute all tasks
        await gather(*sche_groups)

    async def schedule(self):
        await self.__get_results()

        results = {}
        for item in self.queue:
            if item["sche_group"] not in results:
                results[item["sche_group"]] = []
            results[item["sche_group"]].append(item["dut_result"])

        for key in results:
            if len(results[key]) == 1:
                results[key] = results[key][0]

        return results

class AfterModelScheduler(BeforeModelScheduler):
    """
    The After model message scheduler.

    Msg will be executed after it is sent to the Model. Specifically, when an Msg is forwarded to the model, it is
    immediately executed.
    """

    async def wrapped_coro(self, coro, queue_item):
        """
        Wrap the coro so that it can forward the item to the models before it is executed. After both the model and the
        DUT are driven, the results will be compared.
        """

        await self.forward_to_models(queue_item)
        queue_item["dut_result"] = await coro

        driver = queue_item["driver"]
        if driver.need_compare:
            driver.compare_results(queue_item["dut_result"], queue_item["model_results"])

class Env:
    """Provides an environment for operation on the DUT."""

    def __init__(self, monitor_step):
        """
        Args:
            monitor_step: Provide a step function for monitor, and monitor will monitor
                          each step.
        """

        self.drive_queue = []
        self.attached_model = []

        self.monitor_step = monitor_step

        # Env will assign self to all monitor methods
        for monitor_func in self.__all_monitor_method():
            create_task(monitor_func(self, config_env=True))

    def attach(self, model):
        """
        Attach a model to the environment.

        Args:
            model: The model to be attached.

        Returns:
            The environment itself.
        """

        self.__ensure_model_match(model)
        if model.is_attached():
            warning(f"Model {model} is already attached to an environment, the original \
                    environment will be replaced")
            model.attached_env = None

        self.attached_model.append(model)

        return self

    def unattach(self, model):
        """
        Unattach a model from the environment.

        Args:
            model: The model to be unattached.

        Returns:
            The environment itself.
        """

        if model in self.attached_model:
            self.attached_model.remove(model)
            model.attached_env = None
        else:
            error(f"Model {model} is not attached to the environment")

        return self

    def __ensure_model_match(self, model):
        """
        Make sure the model matches the env.

        Args:
            model: The model to be checked.

        Raises:
            ValueError: If the model does not match the env.
        """

        if not isinstance(model, Model):
            raise ValueError(f"Model {model} is not an instance of Model")

        for driver_method in self.__all_driver_method():
            if not driver_method.__is_model_sync__:
                continue

            if driver_method.__is_match_func__:
                if not model.get_driver_func(driver_method.__name_to_match__):
                    raise ValueError(f"Model {model} does not have driver function {driver_method.__name_to_match__}")
            else:
                if not model.get_driver_method(driver_method.__name_to_match__):
                    raise ValueError(f"Model {model} does not have driver method {driver_method.__name_to_match__}")

        for monitor_method in self.__all_monitor_method():
            if not monitor_method.__need_compare__:
                continue

            if not model.get_monitor_method(monitor_method.__name_to_match__):
                raise ValueError(f"Model {model} does not have monitor method {monitor_method.__name_to_match__}")

    def __all_driver_method(self):
        """
        Yields all driver method in the environment.

        Returns:
            A generator that yields all driver method in the environment.
        """

        for attr in dir(self):
            if hasattr(getattr(self, attr), "__is_driver_decorated__"):
                yield getattr(self, attr)

    def __all_monitor_method(self):
        """
        Yields all monitor methods in the environment.

        Returns:
            A generator that yields all monitor method in the environment.
        """

        for attr in dir(self):
            if hasattr(getattr(self, attr), "__is_monitor_decorated__"):
                yield getattr(self, attr)

    async def drive_completed(self, sche_method="model_first"):
        """Drive all the tasks in the drive queue."""

        if sche_method == "model_first":
            result = await ModelFirstScheduler(self, self.drive_queue, self.attached_model).schedule()
        elif sche_method == "before_model":
            result = await BeforeModelScheduler(self, self.drive_queue, self.attached_model).schedule()
        elif sche_method == "after_model":
            result = await AfterModelScheduler(self, self.drive_queue, self.attached_model).schedule()
        else:
            raise ValueError(f"Invalid sche_method {sche_method}")

        self.drive_queue.clear()

        return result


def driver_method(*, model_sync=True, imme_ret=True, match_func=False, \
                  need_compare=False, compare_func=None, name_to_match=None, sche_group=None):
    """
    Decorator for driver method.

    Args:
        model_sync:    Whether to synchronize the driver method with the model.
        imme_ret:      Whether to return immediately.
        match_func:    Whether to match the function.
        need_compare:  Whether to compare the output with the reference.
        compare_func:  The function to implement the comparison. If it is None, the default.
        name_to_match: The name to match the driver method or function in the model.
        sche_group:    The schedule group.

    Returns:
        The decorator for driver method.
    """

    def decorator(func):
        driver = Driver(func, model_sync, imme_ret, match_func, \
                        need_compare, compare_func, name_to_match, sche_group)
        return driver.wrapped_func()
    return decorator

def monitor_method(*, need_compare=True, auto_monitor=True, compare_func=None, name_to_match=None):
    """
    Decorator for monitor method.

    Args:
        need_compare:  Whether to compare the output with the reference.
        auto_monitor:  Whether to monitor automatically. If True, the monitor will monitor the DUT forever in the
                       background.
        compare_func:  The function to implement the comparison. If it is None, the default
                       comparison function will be used.
        name_to_match: The name to match the monitor method.

    Returns:
        The decorator for monitor method.
    """

    def decorator(func):
        monitor = Monitor(func, need_compare, auto_monitor, compare_func, name_to_match)
        return monitor.wrapped_func()
    return decorator
