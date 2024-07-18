from enum import Enum
from .logger import *
from .asynchronous import Event, gather, create_task
from .base import MObject


class PeekableBuffer:
    """
    An asynchronous buffer containing peek functionality.
    """

    def __init__(self, max_size):
        self.buffer = []
        self.max_size = max_size
        self.full_event = Event()
        self.empty_event = Event()

    def size(self):
        """
        Returns the size of the buffer.

        Returns:
            The size of the buffer.
        """

        return len(self.buffer)

    def empty(self):
        """
        Returns whether the buffer is empty.

        Returns:
            True if the buffer is empty, False otherwise.
        """

        return len(self.buffer) == 0

    async def put(self, item):
        """
        Puts an item into the buffer.

        Args:
            item: The item to put into.
        """

        if self.max_size == 0:
            self.buffer.append(item)
            self.empty_event.set()
            await self.full_event.wait()
            self.full_event.clear()
        else:
            while self.max_size != -1 and self.size() >= self.max_size:
                await self.full_event.wait()
                self.full_event.clear()
            self.buffer.append(item)
            self.empty_event.set()

    async def get(self):
        """
        Gets an item from the buffer.

        Returns:
            The item from the buffer
        """

        if self.max_size == 0:
            await self.empty_event.wait()
            self.empty_event.clear()
            item = self.buffer.pop(0)
            self.full_event.set()
            return item
        else:
            while not self.buffer:
                await self.empty_event.wait()
                self.empty_event.clear()
            self.full_event.set()
            return self.buffer.pop(0)

    async def peek(self):
        """
        Peeks an item from the buffer.

        Returns:
            The item from the buffer.
        """

        while not self.buffer:
            await self.item_available.wait()
            self.item_available.clear()
        return self.buffer[0]


class PortCommand(Enum):
    """An enumeration of port commands."""

    AsyncGet = 1
    AsyncPeek = 2
    AsyncPut = 3
    SyncGet = 4
    SyncPeek = 5
    SyncPut = 6
    TryGet = 7
    TryPeek = 8
    TryPut = 9
    CanGet = 10
    CanPeek = 11
    CanPut = 12

    def is_async(self):
        """Whether this command is asynchronous."""

        return self in [PortCommand.AsyncGet, PortCommand.AsyncPeek, PortCommand.AsyncPut]

    def is_single_access(self):
        """Whether the command can be used to access only one port."""

        return not self.is_async() and not self is PortCommand.SyncPut

    def is_put_method(self):
        """
        Whether the command is a put method.
        It is used to determine whether the command requires a parameter.
        """

        return self in [PortCommand.AsyncPut, PortCommand.SyncPut, PortCommand.TryPut]

    def match_func_name(self):
        """Returns the matching function name."""

        return {
            PortCommand.AsyncGet: "get",
            PortCommand.AsyncPeek: "peek",
            PortCommand.AsyncPut: "put",
            PortCommand.SyncGet: "sync_get",
            PortCommand.SyncPeek: "sync_peek",
            PortCommand.SyncPut: "sync_put",
            PortCommand.TryGet: "try_get",
            PortCommand.TryPeek: "try_peek",
            PortCommand.TryPut: "try_put",
            PortCommand.CanGet: "can_get",
            PortCommand.CanPeek: "can_peek",
            PortCommand.CanPut: "can_put",
        }[self]

class Port(MObject):
    """A Port is used to interact between different components."""

    def __init__(self, end_port=True, max_size=0):
        """
        Constructs a port.

        Args:
            end_port: Whether this port is an end port. End port is the port at the
                      end of the communication.
        """

        self.connected_ports = []

        self.__end_port = end_port
        self.__buffer = PeekableBuffer(max_size)
        self.__func_dict = {}

    def set_sync_get(self, func):
        """
        Sets the synchronous get function.

        Args:
            func: The synchronous get function.

        Returns:
            The port itself.
        """

        self.__func_dict[PortCommand.SyncGet] = func
        return self

    def set_sync_peek(self, func):
        """
        Sets the synchronous peek function.

        Args:
            func: The synchronous peek function.

        Returns:
            The port itself.
        """

        self.__func_dict[PortCommand.SyncPeek] = func
        return self

    def set_sync_put(self, func):
        """
        Sets the synchronous put function.

        Args:
            func: The synchronous put function.

        Returns:
            The port itself.
        """

        self.__func_dict[PortCommand.SyncPut] = func
        return self

    def set_try_get(self, func):
        """
        Sets the try get function.

        Args:
            func: The try get function.

        Returns:
            The port itself.
        """

        self.__func_dict[PortCommand.TryGet] = func
        return self

    def set_try_peek(self, func):
        """
        Sets the try peek function.

        Args:
            func: The try peek function.

        Returns:
            The port itself.
        """

        self.__func_dict[PortCommand.TryPeek] = func
        return self

    def set_try_put(self, func):
        """
        Sets the try put function.

        Args:
            func: The try put function.

        Returns:
            The port itself.
        """

        self.__func_dict[PortCommand.TryPut] = func
        return self

    def set_can_get(self, func):
        """
        Sets the can get function.

        Args:
            func: The can get function.

        Returns:
            The port itself.
        """

        self.__func_dict[PortCommand.CanGet] = func
        return self

    def set_can_peek(self, func):
        """
        Sets the can peek function.

        Args:
            func: The can peek function.

        Returns:
            The port itself.
        """

        self.__func_dict[PortCommand.CanPeek] = func
        return self

    def set_can_put(self, func):
        """
        Sets the can put function.

        Args:
            func: The can put function.

        Returns:
            The port itself.
        """

        self.__func_dict[PortCommand.CanPut] = func
        return self

    def connect(self, port: 'Port'):
        """
        Connects this port to another port.

        Args:
            port: The port to connect to.

        Returns:
            The port itself.
        """

        assert isinstance(port, Port), "Port must be an instance of Port"

        self.connected_ports.append(port)
        port.connected_ports.append(self)

        return self

    def disconnect(self, port: 'Port'):
        """
        Disconnects this port from another port.

        Args:
            port: The port to disconnect from.

        Returns:
            The port itself.
        """

        assert isinstance(port, Port), "Port must be an instance of Port"

        if port not in self.connected_ports:
            raise Exception("Port is not connected to the port")

        self.connected_ports.remove(port)
        port.connected_ports.remove(self)

        return self

    def is_leaf(self):
        """
        Returns whether this port is a leaf port. A leaf port is a port that is connected to only one other port.

        Returns:
            True if this port is a leaf port, False otherwise
        """

        return len(self.connected_ports) == 1

    def is_connected(self):
        """
        Returns whether this port is connected to another port.

        Returns:
            True if this port is connected to another port, False otherwise
        """

        return len(self.connected_ports) > 0

    def size(self):
        """
        Returns the size of the buffer in the port.

        Returns:
            The size of the buffer.
        """

        return self.__buffer.size()

    def empty(self):
        """
        Returns whether the buffer is empty.

        Returns:
            True if the buffer is empty, False otherwise.
        """

        return self.__buffer.empty()

    def __should_process(self):
        """
        Returns whether this port should process the item.

        Returns:
            True if this port should process the item, False otherwise.
        """

        return self.is_leaf() or self.__end_port

    def __send(self, cmd: PortCommand, start_port=False, item=None, exception=None):
        """
        Sends the item based on the command.

        Args:
            cmd: The command to send.
            start_port: Whether the port is the start port.
            item: The item to send.
            exception: The exception port to exclude from the send.

        Returns:
            The result of the command
        """

        if (self.__should_process() and not start_port) \
                or (not self.is_connected() and start_port):
            return self.__process(item, cmd)

        if cmd.is_single_access():
            if len(self.connected_ports) > 2:
                raise Exception(f"Multiple paths are found when {cmd} is executed")

            port_to_send = self.connected_ports[0]
            if exception is not None and port_to_send is exception:
                port_to_send = self.connected_ports[1]

            return port_to_send.__send(cmd, False, item, self)

        else:
            for port in self.connected_ports:
                if not port is exception:
                    port.__send(cmd, False, item, self)

    def __process(self, item, cmd: PortCommand):
        """
        Processes the item based on the command.

        it will call the corresponding function in the function dictionary.

        Args:
            item: The item to process.
            cmd: The command to process.

        Returns:
            The result of the command.
        """

        if not self.__end_port:
            warning(f"{cmd.match_func_name()} is called on the non-end port")

        if cmd in self.__func_dict:
            if cmd.is_put_method():
                self.__func_dict[cmd](item)
            else:
                return self.__func_dict[cmd]()
        else:
            raise NotImplementedError(f"{cmd.match_func_name()} is not set")

    async def __async_send(self, cmd: PortCommand, start_port=False, item=None, exception=None):
        """
        Sends the item asynchronously based on the command.

        Args:
            cmd: The command to send.
            start_port: Whether the port is the start port.
            item: The item to send.
            exception: The exception port to exclude from the send.

        Returns:
            The result of the command
        """

        if (self.__should_process() and not start_port) \
                or (not self.is_connected() and start_port):
            return await self.__async_process(item, cmd)

        if cmd == PortCommand.AsyncPut:
            all_task = []
            for port in self.connected_ports:
                if not port is exception:
                    all_task.append(port.__async_send(cmd, False, item, self))
            if len(all_task) > 1:
                await gather(*all_task)
            else:
                await all_task[0]
        else:
            raise Exception("Only AsyncPut is supported")

    async def __async_process(self, item, cmd: PortCommand):
        """
        Processes the item asynchronously based on the command.

        Args:
            item: The item to process.
            cmd: The command to process.

        Returns:
            The result of the command.
        """

        if cmd == PortCommand.AsyncPut:
            if not self.__end_port:
                warning("Item has been put into the non-end port")

            await self.__buffer.put(item)
        else:
            raise NotImplementedError("Only AsyncPut is supported")

    def sync_get(self):
        """
        Synchronous get method.

        Returns:
            The item from the port.
        """

        return self.__send(PortCommand.SyncGet, start_port=True)

    def sync_peek(self):
        """
        Synchronous peek method.

        Returns:
            The item from the port.
        """

        return self.__send(PortCommand.SyncPeek, start_port=True)

    def sync_put(self, item):
        """
        Synchronous put method.

        Args:
            item: The item to put into the port.
        """

        self.__send(PortCommand.SyncPut, start_port=True, item=item)

    def try_get(self):
        """
        Try get method.

        Returns:
            The item from the port.
        """

        return self.__send(PortCommand.TryGet, start_port=True)

    def try_peek(self):
        """
        Try peek method.

        Returns:
            The item from the port.
        """

        return self.__send(PortCommand.TryPeek, start_port=True)

    def try_put(self, item):
        """
        Try put method.

        Args:
            item: The item to put into the port.
        """

        self.__send(PortCommand.TryPut, start_port=True, item=item)

    def can_get(self):
        """
        Can get method.

        Returns:
            True if the port can get, False otherwise.
        """

        return self.__send(PortCommand.CanGet, start_port=True)

    def can_peek(self):
        """
        Can peek method.

        Returns:
            True if the port can peek, False otherwise.
        """

        return self.__send(PortCommand.CanPeek, start_port=True)

    def can_put(self):
        """
        Can put method.

        Returns:
            True if the port can put, False otherwise.
        """

        return self.__send(PortCommand.CanPut, start_port=True)

    async def get(self):
        """
        Asynchronous get method.
        """

        return await self.__buffer.get()

    async def peek(self):
        """
        Asynchronous peek method.
        """

        return await self.__buffer.peek()

    async def put(self, item):
        """
        Asynchronous put method.
        """

        await self.__async_send(PortCommand.AsyncPut, start_port=True, item=item)
