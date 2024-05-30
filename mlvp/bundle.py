import re
from .logger import *
from .triggers import ClockCycles
from .base import MObject

class Bundle(MObject):
    """
    A bundle is a collection of signals in a DUT.
    """

    signals = []

    def __init__(self):
        """
        Create a bundle.
        Users should use from_prefix, from_regex, or from_dict to create a bundle
        instead of calling this method directly.
        """

        self.name = None
        self.clock_event = None
        self.connect_method = None # Method for signal connection.
                                   # It should be "dict", "prefix", or "regex"
        self.method_value = None

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

    async def step(self, ncycles=1):
        """
        Wait for the clock for ncycles.
        Only works if the bundle has a connected signal.

        Args:
            ncycles: The number of cycles to wait.
        """

        if self.clock_event is None:
            critical("cannot use step in bundle without a connected signal")

        await ClockCycles(self.clock_event, ncycles)

    def bind(self, dut, unconnected_signal_access=True):
        """
        Bind the dut's signal to this bundle.

        Args:
            dut: The dut to bind the bundle to.

        Returns:
            The bundle itself.
        """

        self.__bind_from_signal_list(list(self.__all_signals(dut)), self.name,
                                     unconnected_signal_access)
        return self


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
        new_bundle.connect_method = "prefix"
        new_bundle.method_value = prefix
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
        new_bundle.connect_method = "regex"
        new_bundle.method_value = regex
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
        new_bundle.connect_method = "dict"
        new_bundle.method_value = dict
        return new_bundle

    @staticmethod
    def new_list(signal_list):
        """
        Create a new bundle class with a list of signals quickly.

        >>> myBundle = Bundle.new_list(["a", "b", "c"]).from_prefix("io_")

        Args:
            signal_list: A list of signals.

        Returns:
            A new bundle class.
        """

        class NewBundle(Bundle):
            signals = signal_list

        return NewBundle

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


    def __add_signal_attr(self, signal_name, signal, info_bundle_name, info_dut_name):
        """
        Add a signal attribute to the bundle and log the connection.

        Args:
            signal_name: The name of the signal in the bundle.
            signal: The signal itself.
            info_bundle_name: The name of the bundle in the log.
            info_dut_name: The name of the signal in the DUT in the log.
        """

        setattr(self, signal_name, signal)
        if self.clock_event is None:
            self.clock_event = signal.event

        info(f"dut's signal \"{info_dut_name}\" is connected to \"{info_bundle_name}\"")

    def __detect_missing_signals(self, connected_signals, level_string,
                                 unconnected_signal_access):
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
                warning(f"signal \"{Bundle.__appended_level_string(level_string, signal)}\" is not found")
                if unconnected_signal_access:
                    setattr(self, signal, self._dummy_signal)

    def __bind_from_signal_list(self, all_signals, level_string, unconnected_signal_access):
        """
        Bind signals to the bundle from a list of signals.

        Args:
            all_signals: A list of signals to bind.
            level_string: The string of the current level.
            unconnected_signal_access: Whether unconnected signals could be accessed.
        """

        if self.connect_method == "dict":
            all_signals = self.__bind_by_dict(all_signals, self.method_value, level_string,
                                              unconnected_signal_access)
        elif self.connect_method == "prefix":
            all_signals = self.__bind_by_prefix(all_signals, self.method_value, level_string,
                                                unconnected_signal_access)
        elif self.connect_method == "regex":
            all_signals = self.__bind_by_regex(all_signals, self.method_value, level_string,
                                               unconnected_signal_access)
        else:
            raise ValueError("connect_method must be 'dict', 'prefix', or 'regex'")


    def __bind_by_dict(self, all_signals, dict, level_string, unconnected_signal_access):
        """
        Bind signals to the bundle by a dictionary.

        Args:
            all_signals: A list of signals to bind.
            dict: A dictionary to map the signals.
            level_string: The string of the current level.
            unconnected_signal_access: Whether unconnected signals could be accessed.

        Returns:
            A list of signals that are not connected.  The name in the list is changed
            to the key in the dictionary.
        """

        # Filter all the signals contained in the dictionary and connect the signals contained
        # in the bundle. Remain signals that are not connected are added into remain_signals
        connected_signals = []
        remain_signals = []
        for signal in all_signals:
            if signal["name"] in dict.values():
                name = list(dict.keys())[list(dict.values()).index(signal["name"])]

                if name in self.signals:
                    self.__add_signal_attr(name,
                                        signal["signal"],
                                        info_dut_name=signal["org_name"],
                                        info_bundle_name=Bundle.__appended_level_string(
                                            level_string, name))
                    connected_signals.append(name)
                else:
                    remain_signals.append({
                        "name": name,
                        "org_name": signal["org_name"],
                        "signal": signal["signal"]
                    })
        self.__detect_missing_signals(connected_signals, level_string, unconnected_signal_access)

        # Bind the remain signals to the sub-bundles
        for sub_bundle_name, sub_bundle in self.__all_sub_bundles():
            remain_signals = sub_bundle.__bind_from_signal_list(remain_signals,
                                                                Bundle.__appended_level_string(
                                                                    level_string, sub_bundle_name),
                                                                unconnected_signal_access)
            if sub_bundle.clock_event is not None:
                self.clock_event = sub_bundle.clock_event

        return remain_signals


    def __bind_by_prefix(self, all_signals, prefix, level_string, unconnected_signal_access):
        """
        Bind signals to the bundle by prefix.

        Args:
            all_signals: A list of signals to bind.
            prefix: The prefix to match the signals.
            level_string: The string of the current level.
            unconnected_signal_access: Whether unconnected signals could be accessed.

        Returns:
            A list of signals that are not connected. The prefix is removed from the name.
        """

        # Filter all the signals containing prefix and connect the signals contained in the bundle.
        # Remain signals that are not connected are added into remain_signals
        connected_signals = []
        remain_signals = []
        for signal in all_signals:
            if signal["name"].startswith(prefix):
                name_no_prefix = signal["name"][len(prefix):]

                if name_no_prefix in self.signals:
                    self.__add_signal_attr(name_no_prefix,
                                           signal["signal"],
                                           info_dut_name=signal["org_name"],
                                           info_bundle_name=Bundle.__appended_level_string(
                                               level_string, name_no_prefix))
                    connected_signals.append(name_no_prefix)
                else:
                    remain_signals.append({
                        "name": signal["name"][len(prefix):],
                        "org_name": signal["org_name"],
                        "signal": signal["signal"]
                    })
        self.__detect_missing_signals(connected_signals, level_string, unconnected_signal_access)

        # Bind the remain signals to the sub-bundles
        for sub_bundle_name, sub_bundle in self.__all_sub_bundles():
            remain_signals = sub_bundle.__bind_from_signal_list(remain_signals,
                                                                Bundle.__appended_level_string(
                                                                    level_string, sub_bundle_name),
                                                                    unconnected_signal_access)
            if sub_bundle.clock_event is not None:
                self.clock_event = sub_bundle.clock_event

        return remain_signals

    def __bind_by_regex(self, all_signals, regex, level_string, unconnected_signal_access):
        """
        Bind signals to the bundle by regex.

        Args:
            all_signals: A list of signals to bind.
            regex: The regex to match the signals.
            level_string: The string of the current level.
            unconnected_signal_access: Whether unconnected signals could be accessed.

        Returns:
            A list of signals that are not connected. The name is the captured group in the regex.
        """

        # Filter all the signals matching the regex and connect the signals contained in the bundle.
        # Remain signals that are not connected are added into remain_signals
        connect_signals = []
        remain_signals = []
        for signal in all_signals:
            match = re.search(regex, signal["name"])
            if match is not None:
                name = "".join(match.groups())
                if name in self.signals:
                    self.__add_signal_attr(name,
                                           signal["signal"],
                                           info_dut_name=signal["org_name"],
                                           info_bundle_name=Bundle.__appended_level_string(
                                               level_string, name))
                    connect_signals.append(name)
                else:
                    remain_signals.append({
                        "name": name,
                        "org_name": signal["org_name"],
                        "signal": signal["signal"]
                    })
        self.__detect_missing_signals(connect_signals, level_string, unconnected_signal_access)

        # Bind the remain signals to the sub-bundles
        for sub_bundle_name, sub_bundle in self.__all_sub_bundles():
            remain_signals = sub_bundle.__bind_from_signal_list(remain_signals,
                                                                Bundle.__appended_level_string(
                                                                    level_string, sub_bundle_name),
                                                                unconnected_signal_access)
            if sub_bundle.clock_event is not None:
                self.clock_event = sub_bundle.clock_event

        return remain_signals


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
    def __appended_level_string(level_string, level):
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


