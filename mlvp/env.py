from .logger import error, warning
from .model import Model
from .asynchronous import gather, create_task
from .agent import Monitor, Driver

class MsgScheduler:
    """The message scheduler."""

    def __init__(self, queue: list, models: list):
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
    async def __sequential_execution_all(*tasks):
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

    async def __get_dut_results(self):
        """
        Get the results from the DUT.
        It will add the results to the drive queue with the key "dut_result".
        """

        # Group all tasks by function name
        all_tasks = {}
        for index, item in enumerate(self.queue):
            func = item["driver"].drive_func
            func_name = func.__name__

            if func_name not in all_tasks:
                all_tasks[func_name] = []

            all_tasks[func_name].append((index, func(self, *item["args"], **item["kwargs"])))

        # Generate all tasks to be executed
        task_names = []
        task_indexes = []
        tasks_to_exec = []
        for func_name, tasks in all_tasks.items():
            task_names.append(func_name)
            if len(tasks) == 1:
                tasks_to_exec.append(tasks[0][1])
                task_indexes.append([tasks[0][0]])
            else:
                coroutines = [item[1] for item in tasks]
                task_indexes.append([item[0] for item in tasks])
                tasks_to_exec.append(self.__sequential_execution_all(*coroutines))

        # Execute all tasks
        results = await gather(*tasks_to_exec)

        # Add the results to the drive queue
        for func_results, indexes in zip(results, task_indexes):
            if not isinstance(func_results, list):
                func_results = [func_results]

            for index, result in zip(indexes, func_results):
                self.queue[index]["dut_result"] = result

        return dict(zip(task_names, results))

    def __compare_results(self):
        """Compare the results of the DUT and the models."""

        for item in self.queue:
            driver: Driver = item["driver"]
            if driver.result_compare:
                driver.compare_results(item["dut_result"], item["model_results"])

    async def schedule(self):

        await self.__get_model_results()
        dut_result = await self.__get_dut_results()
        self.__compare_results()
        self.queue.clear()

        return dut_result


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
        for func_name in self.__all_monitor_method():
            monitor_func = getattr(self, func_name)
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
            if not monitor_method.__is_model_compare__:
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

    def drive_completed(self):
        """Drive all the tasks in the drive queue."""

        return ModelFirstScheduler(self.drive_queue, self.attached_model).schedule()


def driver_method(*, model_sync=True, imme_ret=True, match_func=False, \
                  result_compare=False, compare_method=None, name_to_match=None, sche_group=None):
    """
    Decorator for driver method.

    Args:
        model_sync: Whether to synchronize the driver method with the model.
        imme_ret: Whether to return immediately.
    """

    def decorator(func):
        driver = Driver(func, model_sync, imme_ret, match_func, \
                        result_compare, compare_method, name_to_match, sche_group)
        return driver.wrapped_func()
    return decorator

def monitor_method(*, model_compare=True, auto_monitor=True, compare_func=None, name_to_match=None):
    """
    Decorator for monitor method.

    Args:
        model_compare: Whether to compare the output with the reference.
        auto_monitor: Whether to monitor automatically. If True, the monitor will
                      monitor the DUT forever in the background.
        compare_func: The function to implement the comparison. If it is None, the default
                      comparison function will be used.

    Returns:
        The decorator for monitor method.
    """

    def decorator(func):
        monitor = Monitor(func, model_compare, auto_monitor, compare_func, name_to_match)
        return monitor.wrapped_func()
    return decorator
