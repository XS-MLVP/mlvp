from .base import MObject
from .logger import error, warning
from .model import Model
from .agent import Agent


class Env(MObject):
    """
    Env is used to wrap the entire verification environment and provides reference model synchronization
    """

    def __init__(self):
        self.attached_models = []

    def attach(self, model):
        """
        Attach a model to the env.

        Args:
            model: The model to be attached.

        Returns:
            The env itself.
        """

        assert isinstance(model, Model), f"Model {model} is not an instance of Model"
        model.collect_all()

        if model.is_attached():
            warning(f"Model {model} is already attached to an env, the original env will be replaced")
            model.attached_env = None
            model.clear_matched()

        self.__inject_all(model)
        self.__ensure_model_match(model)
        self.attached_models.append(model)

        return self

    def unattach(self, model):
        """
        Unattach a model from the env.

        Args:
            model: The model to be unattached.

        Returns:
            The env itself.
        """

        if model in self.attached_model:
            self.__uninject_all(model)
            self.attached_model.remove(model)
            model.clear_matched()
            model.attached_env = None
        else:
            error(f"Model {model} is not attached to the env")

        return self

    def get_agent(self, agent_name):
        """Get the agent by name."""

        if hasattr(self, agent_name):
            agent = getattr(self, agent_name)

            if isinstance(agent, Agent):
                return agent

    def all_agent_names(self):
        """
        Yields all agent names in the env.

        Returns:
            A generator that yields all agent names in the env.
        """

        for attr in dir(self):
            if isinstance(getattr(self, attr), Agent):
                yield attr

    def __inject_driver_method(self, model: Model, agent_name, driver_method):
        """
        Inject hook and port from model to matched driver method.
        """

        driver_path = f"{agent_name}.{driver_method.__name__}"

        model_info = {
            "agent_hook" : model.get_agent_hook(agent_name, mark_matched=True),
            "agent_port" : model.get_agent_port(agent_name, mark_matched=True),
            "driver_hook" : model.get_driver_hook(driver_path, mark_matched=True),
            "driver_port" : model.get_driver_port(driver_path, mark_matched=True)
        }

        driver_method.__driver__.model_infos[model] = model_info

    def __inject_monitor_method(self, model: Model, agent_name, monitor_method):
        """
        Inject port from model to matched monitor method.
        """

        monitor_path = f"{agent_name}.{monitor_method.__name__}"

        model_info = {
            "monitor_port" : model.get_monitor_port(monitor_path, mark_matched=True)
        }

        monitor_method.__monitor__.model_infos[model] = model_info

    def __inject_all(self, model):
        """
        Inject all hooks and ports to the agents.
        """

        for agent_name in self.all_agent_names():
            agent = getattr(self, agent_name)

            for driver_method in agent.all_driver_method():
                self.__inject_driver_method(model, agent_name, driver_method)

            for monitor_method in agent.all_monitor_method():
                self.__inject_monitor_method(model, agent_name, monitor_method)

    def __uninject_all(self, model):
        """
        Uninject all hooks and ports from the agents.
        """

        for agent_name in self.all_agent_names():
            agent = getattr(self, agent_name)

            for driver_method in agent.all_driver_method():
                driver_method.__driver__.model_infos.pop(model)

            for monitor_method in agent.all_monitor_method():
                monitor_method.__monitor__.model_infos.pop(model)

    def __ensure_env_monitor_match(self, model):
        """
        Make sure the all monitor_method in env has matched monitor_port in model.
        """

        for agent_name in self.all_agent_names():
            agent = getattr(self, agent_name)

            for monitor_method in agent.all_monitor_method():
                monitor_path = f"{agent_name}.{monitor_method.__name__}"

                if monitor_method.__monitor__.model_infos[model].get("monitor_port") is None:
                    raise ValueError(f"Monitor Method \"{monitor_path}\" is not matched to any monitor port in model")

    def __ensure_single_driver_match(self, driver, model):
        """
        Make sure the driver is matched corif rectly to model.
        """

        model_info = driver.model_infos[model]

        if model_info.get("agent_port") is not None:
            if model_info.get("driver_port") is not None:
                raise ValueError(f"Agent port \"{model_info['agent_port'].name}\" and driver port "
                                 f"\"{model_info['driver_port'].name}\" should not be set at the same time")

            if model_info.get("agent_hook") is not None:
                raise ValueError(f"Agent port \"{model_info['agent_port'].name}\" and agent hook "
                                 f"\"{model_info['agent_hook'].__agent_name__}\" should not be set at the same time")

            if model_info.get("driver_hook") is not None:
                raise ValueError(f"Agent port \"{model_info['agent_port'].name}\" and driver hook "
                                 f"\"{model_info['driver_hook'].__driver_path__}\" should not be set at the same time")

        if model_info.get("driver_port") is not None:
            if model_info.get("agent_hook") is not None:
                raise ValueError(f"Driver port \"{model_info['driver_port'].name}\" and agent hook "
                                 f"\"{model_info['agent_hook'].__agent_name__}\" should not be set at the same time")

            if model_info.get("driver_hook") is not None:
                raise ValueError(f"Driver port \"{model_info['driver_port'].name}\" and driver hook "
                                 f"\"{model_info['driver_hook'].__driver_path__}\" should not be set at the same time")

        if model_info.get("agent_hook") is None \
            and model_info.get("driver_hook") is None \
            and model_info.get("agent_port") is None \
            and model_info.get("driver_port") is None:
            raise ValueError(f"Driver Method \"{driver.__name__}\" is not matched to any port or hook in model")

    def __ensure_env_driver_match(self, model):
        """
        Make sure the all driver_method in env has matched correctly to model.
        """

        for agent_name in self.all_agent_names():
            agent = getattr(self, agent_name)

            for driver_method in agent.all_driver_method():
                driver = driver_method.__driver__

                self.__ensure_single_driver_match(driver, model)

    def __ensure_model_match(self, model: Model):
        """
        Make sure the model matches the env. This function should be called after injecting.

        Args:
            model: The model to be checked.

        Raises:
            ValueError: If the model does not match the env.
        """

        self.__ensure_env_monitor_match(model)
        self.__ensure_env_driver_match(model)
        model.ensure_all_matched()
