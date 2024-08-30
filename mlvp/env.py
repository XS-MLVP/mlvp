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

        for agent_name in dir(self):
            agent = getattr(self, agent_name)

            if isinstance(agent, Agent):
                agent.name = agent_name

    def attach(self, model):
        """
        Attach a model to the env.

        Args:
            model: The model to be attached.

        Returns:
            The env itself.
        """

        if model.is_attached():
            warning(f"Model {model} is already attached to an env, the original env will be replaced")
            model.attached_env = None

        self.__inject_all(model, detected=False)
        self.attached_models.append(model)

        return self

    def unattach(self, model):
        """
        Unattach a model from the env.

        Args:
            model: The model to be unattached.

        Returns:
            The envitself.
        """

        if model in self.attached_model:
            self.attached_model.remove(model)
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

    def __inject_driver_method(self, model: Model, agent_name, driver_method, detected):
        """
        Inject hook and port from model to matched driver method.
        """

        driver_path = f"{agent_name}.{driver_method.__name__}"

        model_info = {
            "agent_hook" : model.get_agent_hook(agent_name),
            "agent_port" : model.get_agent_port(agent_name),
            "driver_hook" : model.get_driver_hook(driver_path),
            "driver_port" : model.get_driver_port(driver_path)
        }

        if not detected:
            driver_method.__driver__.model_infos[model] = model_info

    def __inject_monitor_method(self, model: Model, agent_name, monitor_method, detected):
        """
        Inject port from model to matched monitor method.
        """

        monitor_path = f"{agent_name}.{monitor_method.__name__}"

        model_info = {
            "monitor_port" : model.get_monitor_port(monitor_path)
        }

        if not detected:
            monitor_method.__monitor__.model_infos[model] = model_info

    def __inject_all(self, model, detected):
        """
        Inject all hooks and ports to the agents.
        """

        for agent_name in self.all_agent_names():
            agent = getattr(self, agent_name)

            for driver_method in agent.all_driver_method():
                self.__inject_driver_method(model, agent_name, driver_method, detected)

            for monitor_method in agent.all_monitor_method():
                self.__inject_monitor_method(model, agent_name, monitor_method, detected)

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

        for driver_method in self.all_driver_method():
            if not driver_method.__is_model_sync__:
                continue

            if driver_method.__is_match_func__:
                if not model.get_driver_func(driver_method.__name_to_match__):
                    raise ValueError(f"Model {model} does not have driver function {driver_method.__name_to_match__}")
            else:
                if not model.get_driver_method(driver_method.__name_to_match__):
                    raise ValueError(f"Model {model} does not have driver method {driver_method.__name_to_match__}")

        for monitor_method in self.all_monitor_method():
            if not monitor_method.__need_compare__:
                continue

            if not model.get_monitor_method(monitor_method.__name_to_match__):
                raise ValueError(f"Model {model} does not have monitor method {monitor_method.__name_to_match__}")
