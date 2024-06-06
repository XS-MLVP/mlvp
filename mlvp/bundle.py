import re
from enum import Enum
from .logger import *
from .triggers import ClockCycles
from .base import MObject

class BindMethod(MObject):
    """
    A bind method is a way to connect signals to a bundle.
    """

    def __init__(self, method, value):
        self.method = method
        self.method_value = value

    def bind(self, bundle, all_signals, level_string, detection_mode):
        """
        Bind the signals to the bundle.

        Args:
            bundle: The bundle to bind the signals to.
            all_signals: A list of signals to bind.
            level_string: The string of the current level.
            detection_mode: Whether the method is in detection mode. if it is, the bundle
                            will not be connected to the signals.

        Returns:
            A tuple of three lists:
            - A list of connected signals.
            - A list of matching signals that are not connected.  The item's name in this
              list is changed.
            - A list of signals that are not matched.
        """

        raise NotImplementedError

class PrefixBindMethod(BindMethod):
    """
    A bind method that connects signals to a bundle by matching the prefix of the signal name.
    """

    def __init__(self, prefix):
        super().__init__("prefix", prefix)

    def bind(self, bundle, all_signals, level_string, detection_mode):
        connected_signals = [] # Matched and connected signals
        matching_signals = []  # Matched but not connected signals,
                               # item's name in the list is the name without prefix
        remain_signals = []    # Not matched signals

        prefix = self.method_value
        for signal in all_signals:
            if signal["name"].startswith(prefix):
                name_no_prefix = signal["name"][len(prefix):]

                if name_no_prefix in bundle.signals:
                    if not detection_mode:
                        bundle.add_signal_attr(name_no_prefix,
                                                 signal["signal"],
                                                 info_dut_name=signal["org_name"],
                                                 info_bundle_name=Bundle.appended_level_string(
                                                    level_string, name_no_prefix))
                        connected_signals.append(name_no_prefix)
                else:
                    matching_signals.append({
                        "name": signal["name"][len(prefix):],
                        "org_name": signal["org_name"],
                        "signal": signal["signal"]
                    })
            else:
                remain_signals.append(signal)

        return (connected_signals, matching_signals, remain_signals)

class RegexBindMethod(BindMethod):
    """
    A bind method that connects signals to a bundle by matching the regex of the signal name.
    """

    def __init__(self, regex):
        super().__init__("regex", regex)

    def bind(self, bundle, all_signals, level_string, detection_mode):
        connected_signals = [] # Matched and connected signals
        matching_signals = []  # Matched but not connected signals,
                               # item's name in the list is the name in the captured group
        remain_signals = []    # Not matched signals

        regex = self.method_value
        for signal in all_signals:
            match = re.search(regex, signal["name"])
            if match is not None:
                name = "".join(match.groups())
                if name in bundle.signals:
                    if not detection_mode:
                        bundle.add_signal_attr(name,
                                                 signal["signal"],
                                                 info_dut_name=signal["org_name"],
                                                 info_bundle_name=Bundle.appended_level_string(
                                                     level_string, name))
                    connected_signals.append(name)
                else:
                    matching_signals.append({
                        "name": name,
                        "org_name": signal["org_name"],
                        "signal": signal["signal"]
                    })
            else:
                remain_signals.append(signal)

        return (connected_signals, matching_signals, remain_signals)

class DictBindMethod(BindMethod):
    """
    A bind method that connects signals to a bundle by matching the dictionary.
    """

    def __init__(self, dict):
        super().__init__("dict", dict)

    def bind(self, bundle, all_signals, level_string, detection_mode):
        connected_signals = [] # Matched and connected signals
        matching_signals = []  # Matched but not connected signals,
                               # item's name in the list is the name without prefix
        remain_signals = []    # Not matched signals

        dict = self.method_value
        for signal in all_signals:
            if signal["name"] in dict.values():
                name = list(dict.keys())[list(dict.values()).index(signal["name"])]

                if name in bundle.signals:
                    if not detection_mode:
                        bundle.add_signal_attr(name,
                                                 signal["signal"],
                                                 info_dut_name=signal["org_name"],
                                                 info_bundle_name=Bundle.appended_level_string(
                                                     level_string, name))
                    connected_signals.append(name)
                else:
                    matching_signals.append({
                        "name": name,
                        "org_name": signal["org_name"],
                        "signal": signal["signal"]
                    })
            else:
                remain_signals.append(signal)

        return (connected_signals, matching_signals, remain_signals)


class WriteMode(Enum):
    """
    The write mode of a bundle.
    """

    Imme = 0
    Rise = 1
    Fall = 2

class IOType(Enum):
    """
    The IO type of a bundle.
    """

    Input = 0
    Output = 1
    InOut = 2

class Bundle(MObject):
    """
    A bundle is a collection of signals in a DUT.
    """

    signals = []

    def __init__(self):
        """
        Create a bundle.
        Instances created using this method are matched directly in bind. The create
        instance method provided by from_dict, from_prefix and from_regex enable easier connections.
        """

        self.name = ""     # The name of the bundle
        self.bound = False # Whether the bundle is bound to a DUT

        self.__clock_event = None
        self.__connect_method = PrefixBindMethod("")

    def set_name(self, name):
        """
        Set the name of the bundle.

        Args:
            name: The name of the bundle.

        Returns:
            The bundle itself.
        """

        self.name = name
        return self

    def set_prefix(self, prefix=""):
        """
        Set the bundle to bind from prefix.

        Args:
            prefix: The prefix to match the signals.

        Returns:
            The bundle itself.
        """

        self.__connect_method = PrefixBindMethod(prefix)
        return self

    def set_regex(self, regex=r""):
        """
        Set the bundle to bind from regex.

        Args:
            regex: The regex to match the signals.

        Returns:
            The bundle itself.
        """

        self.__connect_method = RegexBindMethod(regex)
        return self

    def set_dict(self, dict={}):
        """
        Set the bundle to bind from a dictionary.

        Args:
            dict: The dictionary to guide bundle connections

        Returns:
            The bundle itself.
        """

        self.__connect_method = DictBindMethod(dict)
        self.__check_dict_value(dict)
        return self

    def set_write_mode(self, write_mode: WriteMode):
        """
        Set the write mode of the bundle. it will change the write mode of all signals
        in the bundle.

        Args:
            write_mode: The write mode to set.

        Returns:
            The bundle itself.
        """

        for _, signal in self.all_signals():
            if signal.mIOType != IOType.Output:
                signal.write_mode = write_mode

    async def step(self, ncycles=1):
        """
        Wait for the clock for ncycles.
        Only works if the bundle has a connected signal.

        Args:
            ncycles: The number of cycles to wait.
        """

        if self.__clock_event is None:
            critical("cannot use step in bundle without a connected signal")

        await ClockCycles(self.__clock_event, ncycles)

    def bind(self, dut, unconnected_signal_access=True):
        """
        Bind the dut's signal to this bundle. it will overwrites the previous bind.

        Args:
            dut: The dut to bind the bundle to.
            unconnected_signal_access: Whether unconnected signals could be accessed.

        Returns:
            The bundle itself.
        """

        if self.bound:
            warning("bundle is already bound, the previous bind will be overwritten")
            self.__unbind_all()
        else:
            # When first bind, set all sub-bundles' name
            for sub_bundle_name, sub_bundle in self.__all_sub_bundles():
                sub_bundle.set_name(sub_bundle_name)

        self.__bind_from_signal_list(list(self.__all_signals(dut)), self.name,
                                     [], unconnected_signal_access, False, None)
        self.bound = True
        return self

    def as_dict(self, multilevel=True):
        """
        Collect all signals values into a dictionary.

        Args:
            multilevel: When multilevel is true, the subbundle signal values are put
                        into a secondary dictionary. Otherwise, the dictionary returned
                        will have only one level, with the sub-bundles separated by dots
                        in keys.

        Returns:
            A dictionary of all signals values in the bundle.
        """

        if multilevel:
            signals = {signal: getattr(self, signal).value for signal in self.signals}
            sub_bundles = {sub_bundle_name: getattr(self, sub_bundle_name).as_dict(multilevel)
                           for sub_bundle_name, _ in self.__all_sub_bundles()}
            return {**signals, **sub_bundles}
        else:
            signals = {signal: getattr(self, signal).value for signal in self.signals}
            for sub_bundle_name, sub_bundle in self.__all_sub_bundles():
                sub_bundle_dict = sub_bundle.as_dict(multilevel)
                for sub_bundle_signal, value in sub_bundle_dict.items():
                    signals[f"{sub_bundle_name}.{sub_bundle_signal}"] = value
            return signals

    def set_all(self, value):
        """
        Set all signals values to a value, including sub-bundles.

        Args:
            value: The value to set.
        """

        for _, signal in self.all_signals():
            if signal.mIOType != IOType.Output:
                signal.value = value

    def assign(self, dict, multilevel=True):
        """
        Assign all signals values.

        Args:
            dict: The dictionary to assign the signals. if "*" is in the dictionary,
                    the value of "*" will be assigned to all signals that are not in the dictionary.
            multilevel: When multilevel is true, the subbundle signal values are taken
                        from a secondary dictionary. Otherwise, the dictionary should have
                        only one level, with the sub-bundles separated by dots in keys.
        """

        if "*" in dict:
            self.set_all(dict["*"])
            del dict["*"]

        if multilevel:
            for signal, value in dict.items():
                if signal in self.signals:
                    getattr(self, signal).value = value
                elif any(subbundle[0]==signal for subbundle in self.__all_sub_bundles()):
                    getattr(self, signal).assign(value)
        else:
            for signal, value in dict.items():
                if signal in self.signals:
                    getattr(self, signal).value = value
                else:
                    sub_bundle_name, sub_bundle_signal = signal.split(".", 1)
                    getattr(self, sub_bundle_name).assign({sub_bundle_signal: value})

    def detect_connectivity(self, signal_name):
        """
        Detect wether a signal name could be connected to this bundle.

        Args:
            bundle: The bundle to connect.
            signal_name: The name of the signal to connect.

        Returns:
            True if the signal name could be connected to the bundle, False otherwise.
        """

        all_signals = [{
            "name": signal_name,
            "org_name": signal_name,
            "signal": None
        }]

        all_signals = self.__bind_from_signal_list(all_signals, self.name, [], False, True, None)

        return len(all_signals) == 0

    def all_signals_rule(self):
        pass

    def detect_specific_connectivity(self, signal_name, specific_signal):
        """
        Detects whether a signal name can be connected to a specific signal in the bundle
        """

        all_signals = [{
            "name": signal_name,
            "org_name": signal_name,
            "signal": None
        }]

        all_signals = self.__bind_from_signal_list(all_signals, "", [], False, True, specific_signal)

        return len(all_signals) == 0

    @classmethod
    def from_prefix(cls, prefix=""):
        """
        Create a bundle from a prefix.

        Args:
            prefix: The prefix to match the signals.

        Returns:
            A new bundle.
        """

        new_bundle = cls()
        new_bundle.__connect_method = PrefixBindMethod(prefix)
        return new_bundle

    @classmethod
    def from_regex(cls, regex=r""):
        """
        Create a bundle from a regex.
        The signals captured in the regex will be used for matching. If there are
        multiple capture groups, they are concatenated into a string to match.

        Args:
            regex: The regex to match the signals.

        Returns:
            A new bundle.
        """

        new_bundle = cls()
        new_bundle.__connect_method = RegexBindMethod(regex)
        return new_bundle

    @classmethod
    def from_dict(cls, dict={}):
        """
        Create a bundle from a dictionary.
        The keys of the dictionary are the names of the signals in the bundle,
        and the values are the names of the signals in DUT.

        Args:
            dict: The dictionary to guide bundle connections

        Returns:
            A new bundle.
        """

        new_bundle = cls()
        new_bundle.__connect_method = DictBindMethod(dict)
        new_bundle.__check_dict_value(dict)
        return new_bundle

    @staticmethod
    def new_class_from_list(signal_list):
        """
        Create a new bundle class with a list of signals quickly.

        >>> myBundle = Bundle.new_class_from_list(["a", "b", "c"]).from_prefix("io_")

        Args:
            signal_list: A list of signals.

        Returns:
            A new bundle class.
        """

        class NewBundle(Bundle):
            signals = signal_list

        return NewBundle

    def all_signals(self, level_string=""):
        """
        Yield all signals of the bundle.

        Returns:
            A generator of signal names.
        """

        for signal in self.signals:
            yield (Bundle.appended_level_string(level_string, signal)), getattr(self, signal)
        for sub_bundle_name, sub_bundle in self.__all_sub_bundles():
            yield from sub_bundle.all_signals(Bundle.appended_level_string(level_string, sub_bundle_name))

    def add_signal_attr(self, signal_name, signal, info_bundle_name, info_dut_name):
        """
        Add a signal attribute to the bundle and log the connection.

        Args:
            signal_name: The name of the signal in the bundle.
            signal: The signal itself.
            info_bundle_name: The name of the bundle in the log.
            info_dut_name: The name of the signal in the DUT in the log.
        """

        setattr(self, signal_name, signal)
        if self.__clock_event is None:
            self.__clock_event = signal.event

        info(f"dut's signal \"{info_dut_name}\" is connected to \"{info_bundle_name}\"")

    def __str__(self):
        signals = ", ".join([f"{signal}: {getattr(self, signal)}" for signal in self.signals])
        sub_bundles = ", ".join([f"{sub_bundle_name}: {getattr(self, sub_bundle_name)}"
                                 for sub_bundle_name, _ in self.__all_sub_bundles()])
        if sub_bundles != "":
            signals = signals + ", " + sub_bundles
        return f"{type(self).__name__}({signals})"

    def __all_sub_bundles(self):
        """
        Yield all sub-bundles of the bundle.

        Returns:
            A generator of tuples (attr_name, sub_bundle) where attr is the name of the
            sub-bundle and sub_bundle is the sub-bundle itself.
        """

        for attr in dir(self):
            if isinstance(getattr(self, attr), Bundle):
                yield (attr, getattr(self, attr))

    def __detect_missing_signals(self, connected_signals, level_string,
                                 rule_stack, unconnected_signal_access):
        """
        Detect missing signals in the bundle. Log a warning if a signal is not found.
        When unconnected_signal_access is True, set the unconnected signals as dummy
        signals.

        Args:
            connected_signals: A list of connected signals.
            level_string: The string of the current level.
            unconnected_signal_access: Whether unconnected signals could be accessed.
        """

        class DummySignal:
            """
            A dummy signal class that does nothing. It will return None when accessed,
            and do nothing when set.
            """

            def __setattr__(self, __name, __value):
                pass
            def __getattribute__(self, __name):
                return None

        self._dummy_signal = DummySignal()

        for signal in self.signals:
            if signal not in connected_signals:
                rule_string = Bundle.__get_rule_string(rule_stack, signal)
                warning(f"The signal that can be connected to \"{Bundle.appended_level_string(level_string, signal)}\" "
                        f"is not found in dut, it should satisfy rule \"{rule_string}\"")

                if unconnected_signal_access:
                    setattr(self, signal, self._dummy_signal)

    def __unbind_all(self):
        """
        Unbind all signals to the bundle.
        """

        for signal in self.signals:
            if hasattr(self, signal):
                delattr(self, signal)
        for _, sub_bundle in self.__all_sub_bundles():
            sub_bundle.__unbind_all()

    def __bind_from_signal_list(self, all_signals, level_string, rule_stack,
                                unconnected_signal_access, detection_mode, specific_signal):
        """
        Bind the signals to the bundle.

        Args:
            all_signals: A list of signals to bind.
            level_string: The string of the current level.
            rule_stack: The stack of rules to bind the signals.
            unconnected_signal_access: Whether unconnected signals could be accessed.
            detection_mode: Whether the method is in detection mode. if it is, the bundle
                            will not be connected to the signals.

        Returns:
            A list of signals that are not matched.
        """

        rule_stack = rule_stack + [self]
        connected_signals, matching_signals, remain_signals = \
            self.__connect_method.bind(self, all_signals, level_string, detection_mode)

        if not detection_mode:
            self.__detect_missing_signals(connected_signals, level_string,
                                        rule_stack, unconnected_signal_access)

            if specific_signal is not None:
                error("specific signal could only be used in detection mode")
        else:
            if specific_signal is not None:
                remain_signals += connected_signals
                connected_signals = []

                for signal in remain_signals:
                    full_signal_name = Bundle.appended_level_string(level_string, signal["name"])
                    if full_signal_name == specific_signal:
                        connected_signals.append(signal)
                        remain_signals.remove(signal)

        # Bind the remain signals to the sub-bundles
        for sub_bundle_name, sub_bundle in self.__all_sub_bundles():
            matching_signals = sub_bundle.__bind_from_signal_list(matching_signals,
                                                                  Bundle.appended_level_string(
                                                                      level_string, sub_bundle_name),
                                                                  rule_stack, unconnected_signal_access,
                                                                  detection_mode, specific_signal)
            if sub_bundle.__clock_event is not None:
                self.__clock_event = sub_bundle.__clock_event

        Bundle.__revert_signal_name(matching_signals, all_signals)
        return matching_signals + remain_signals


    def __check_dict_value(self, dict):
        """
        Check if the values of the dictionary are valid.

        Args:
            dict: The dictionary to check.
        """

        signal_list = [{
            "name": value,
            "org_name": key,
            "signal": None
        } for key, value in dict.items()]

        unconnected_signals = self.__bind_from_signal_list(signal_list, self.name, [], False, True, None)
        unconnected_signal_names = [signal["org_name"] for signal in unconnected_signals]

        if len(unconnected_signal_names) > 0:
            warning(f"The signal names {unconnected_signal_names} in {type(self).__name__}'s connection dictionary "
                    "are invalid, because they cannot match any signals from the Bundle")

    @staticmethod
    def appended_level_string(level_string, level):
        """
        Append a string to the current level string.

        Args:
            level_string: The current level string.
            level: The string to append.

        Returns:
            The appended string.
        """

        if level_string == "":
            return level
        else:
            return f"{level_string}.{level}"

    @staticmethod
    def __revert_signal_name(signal_list, last_signal_list):
        """
        Change the item's name in signal_list to the item's name in last_signal_list, if it has the
        same original name.

        Args:
            signal_list: A list of signals to revert. this is a list of dictionaries
                         containing the name, original name, and signal pin of the signal.
            last_signal_list: The structure of the last signal list is the same as the signal_list.
        """

        for signal in signal_list:
            for last_signal in last_signal_list:
                if signal["org_name"] == last_signal["org_name"]:
                    signal["name"] = last_signal["name"]


    @staticmethod
    def __is_instance_of_xpin(signal):
        """
        Check if the signal is an instance of XPin. XPin is a class from dut generated by picker
        that represents a signal in a simulation.

        Args:
            signal: The signal to check.

        Returns:
            True if the signal is an instance of XPin, False otherwise.
        """

        return hasattr(signal, "xdata") and hasattr(signal, "event")

    @staticmethod
    def __all_signals(dut):
        """
        Yield all signals of the dut.

        Args:
            dut: The dut to get signals from.

        Returns:
            A generator of dictionaries containing the name, original name, and signal of the signal.
        """

        for attr in dir(dut):
            signal = getattr(dut, attr)
            if not callable(signal) and Bundle.__is_instance_of_xpin(signal):
                yield {
                    "name": attr,
                    "org_name": attr,
                    "signal": signal
                }

    @staticmethod
    def __get_rule_string(rule_stack, signal):
        """
        Get the rule string from the rule stack.

        Args:
            rule_stack: The stack of rules.
            signal: The signal to get the rule string.

        Returns:
            The rule string.
        """

        rule_string = ""
        rule_stack = rule_stack + [signal]

        for index, rule in enumerate(rule_stack):
            if rule is rule_stack[-1] or rule.__connect_method.method == "prefix":
                rule_string += rule if rule is rule_stack[-1] else rule.__connect_method.method_value
            elif rule.__connect_method.method == "dict":
                relative_signal_name = Bundle.__get_path_from_rule_stack(rule_stack[index:])
                flitered_dict = rule_stack[index].__filter_signals_in_dict(rule.__connect_method.method_value,
                                                                      relative_signal_name)

                dict_string = f"<No Matching Signal in Dict>"
                if len(flitered_dict) > 0:
                    dict_string = "|".join([f"{value}" for _, value in flitered_dict.items()])
                    if len(flitered_dict) > 1:
                        dict_string = f"({dict_string})"

                rule_string += dict_string
                break
            elif rule.__connect_method.method == "regex":
                rule_string += f"{rule.__connect_method.method_value} -> "
            else:
                raise ValueError(f"rule must be 'dict', 'prefix', or 'regex'")

        return rule_string

    def __filter_signals_in_dict(self, dict, could_connected_to):
        filtered_dict = {}
        for key, value in dict.items():
            if self.detect_specific_connectivity(key, could_connected_to):
                filtered_dict[key] = value
        return filtered_dict

    @staticmethod
    def __get_path_from_rule_stack(rule_stack, signal=""):
        path = ""
        if signal is not "":
            rule_stack = rule_stack + [signal]

        for rule in rule_stack[1:]:
            if rule is rule_stack[-1]:
                path += rule
            else:
                path += rule.name + "."

        return path




class OldBundle:
    signals_list = []
    sub_bundles = []

    @staticmethod
    def __check_signal(signal):
        for attr in ("xdata", "event"):
            assert hasattr(signal, attr), f"signal \"{signal}\" must have be a Pin"

    def __first_connected_signal(self):
        for sub_bundle_name, _ in self.sub_bundles:
            first_signal = getattr(self, sub_bundle_name).__first_connected_signal()
            if first_signal is not None:
                return first_signal
        for signal in self.signals_list:
            if hasattr(self, signal):
                return getattr(self, signal)
        return None

    def __set_clock_event(self):
        first_connected_signal = self.__first_connected_signal()
        if first_connected_signal is not None:
            self.clock_event = first_connected_signal.event
        else:
            self.clock_event = None

    def __check_unconnected(self, allow_unconnected):
        for signal in self.signals_list:
            if getattr(self, signal) is None:
                if not allow_unconnected:
                    raise ValueError(f"signal \"{signal}\" is not connected")
                warning(f"signal \"{signal}\" is not connected")

    def __str__(self):
        return type(self).__name__ + "(\n" + \
             "\n".join([f"{signal}: {getattr(self, signal)}" for signal in self.signals_list]) + \
             "\n)\n"


    def __init__(self, dut_ports = {},
                 without_check = False,
                 allow_unconnected = True,
                 allow_unconnected_access = True):
        """Create an bundle from a dut with a dictionary to map signals to ports"""

        # set sub-bundles as attributes
        assert len(self.sub_bundles) > 0 or len(self.signals_list) > 0, "sub_bundles or signals_list must not be empty"
        for sub_bundle_name, sub_bundle_creator in self.sub_bundles:
            setattr(self, sub_bundle_name, sub_bundle_creator(dut_ports))

        # set signals as attributes
        for signal in self.signals_list:
            if signal in dut_ports:
                Bundle.__check_signal(dut_ports[signal])
                info(f"signal \"{signal}\" is connected")
                setattr(self, signal, dut_ports[signal])
            else:
                setattr(self, signal, None)

        # check if all signals are connected
        if not without_check:
            self.__check_unconnected(allow_unconnected)

        # set clock event
        self.__set_clock_event()

        # set unconnected signals as dummy signals
        if allow_unconnected_access:
            class DummySignal:
                def __setattr__(self, __name, __value):
                    pass
                def __getattribute__(self, __name):
                    return None
            self._dummy_signal = DummySignal()
            for signal in self.signals_list:
                if getattr(self, signal) is None:
                    setattr(self, signal, self._dummy_signal)


    async def Step(self, ncycles = 1):
        """Wait for the clock for ncycles"""

        assert self.clock_event is not None, "bundle must have one connected signal"
        await ClockCycles(self.clock_event, ncycles)

    def collect(self):
        """Collect all signals values"""

        signals = {signal: getattr(self, signal).value for signal in self.signals_list}
        sub_bundles = {sub_bundle_name: getattr(self, sub_bundle_name).collect() for sub_bundle_name, _ in self.sub_bundles}
        return {**signals, **sub_bundles}

    def assign(self, signals):
        """Assign all signals values"""

        for signal in self.signals_list:
            if signal in signals:
                getattr(self, signal).value = signals[signal]
        for sub_bundle_name, _ in self.sub_bundles:
            if sub_bundle_name in signals:
                getattr(self, sub_bundle_name).assign(signals[sub_bundle_name])


    @classmethod
    def from_prefix(cls, dut, prefix = "",
                    without_check = False,
                    allow_unconnected = True,
                    allow_unconnected_access = True):
        """Create an bundle from a dut or ports_list with a prefix in its signals"""

        if not isinstance(dut, dict):
            dut = cls._get_dut_ports_list(dut)

        return cls._from_prefix_ports_list(dut, prefix,
                                           without_check, allow_unconnected, allow_unconnected_access)

    @classmethod
    def from_regex(cls, dut, regex = r"",
                   without_check = False,
                   allow_unconnected = True,
                   allow_unconnected_access = True):
        """Create an bundle from a dut or ports_list with a regex matching its signals"""

        if not isinstance(dut, dict):
            dut = cls._get_dut_ports_list(dut)

        return cls._from_regex_ports_list(dut, regex,
                                          without_check, allow_unconnected, allow_unconnected_access)

    @classmethod
    def _from_prefix_ports_list(cls, ports_list, prefix = "",
                               without_check = False,
                               allow_unconnected = False,
                               allow_unconnected_access = False):
        """Create an bundle from a ports list with a prefix in its signals"""

        ports = {}
        for signal_name, signal_value in ports_list.items():
            if signal_name.startswith(prefix):
                signal = signal_name[len(prefix):]
                ports[signal] = signal_value

        return cls(dut_ports = ports, without_check = without_check,
                   allow_unconnected = allow_unconnected,
                   allow_unconnected_access = allow_unconnected_access)

    @classmethod
    def _from_regex_ports_list(cls, ports_list, regex = r"",
                               without_check = False,
                               allow_unconnected = False,
                               allow_unconnected_access = False):
        """Create an bundle from a ports list with a regex matching its signals"""

        ports = {}
        for signal_name, signal_value in ports_list.items():
            match = re.search(regex, signal_name)
            if match is not None:
                signal = "".join(match.groups())
                ports[signal] = signal_value

        return cls(dut_ports = ports, without_check = without_check,
                   allow_unconnected = allow_unconnected,
                   allow_unconnected_access = allow_unconnected_access)


    @classmethod
    def _get_dut_ports_list(cls, dut):
        ports_list = {}
        for attr in dir(dut):
            if not callable(getattr(dut, attr)):
                ports_list[attr] = getattr(dut, attr)
        return ports_list


