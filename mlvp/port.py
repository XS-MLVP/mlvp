from enum import Enum
from .logger import *
from .asynchronous import Queue, Event, gather, create_task
from .base import MObject


class PeekableBuffer:
    """
    An asynchronous buffer containing peek functionality.
    """

    def __init__(self):
        self.buffer = []
        self.item_available = Event()

    async def put(self, item):
        """
        Puts an item into the buffer.

        Args:
            item: The item to put into.
        """

        self.buffer.append(item)
        self.item_available.set()

    async def get(self):
        """
        Gets an item from the buffer.

        Returns:
            The item from the buffer
        """

        while not self.buffer:
            await self.item_available.wait()
            self.item_available.clear()
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


class Port(MObject):

    def __init__(self):
        self.connected_ports = []
        self.port_to_get = None

        self.__buffer = PeekableBuffer()


    def connect(self, port: 'Port'):
        """
        Connects this port to another port.

        Args:
            port: The port to connect to.

        Returns:
            The port itself.
        """

        assert isinstance(port, Port), "Port must be an instance of Port"

        for (p1, p2) in [(self, port), (port, self)]:
            p1.connected_ports.append(p2)
            if p1.port_to_get is None:
                p1.port_to_get = p2

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

    def __send(self, cmd: PortCommand, force_forward=False, item=None, exception=None):
        if not self.is_connected():
            raise Exception("Port is not connected to any other port")

        if self.is_leaf() and not force_forward:
            return self.__process(item, cmd)

        ret = None
        for port in self.connected_ports:
            if port is exception:
                continue

            item = port.__send(cmd, False, item, self)
            if port is self.port_to_get:
                ret = item

        return ret

    def __process(self, item, cmd: PortCommand):
        # TODO
        raise NotImplementedError("Port must implement __process method")

    async def __async_send(self, cmd: PortCommand, force_forward=False, item=None, exception=None):
        if not self.is_connected():
            raise Exception("Port is not connected to any other port")

        if self.is_leaf() and not force_forward:
            await self.__async_process(item, cmd)

        if cmd == PortCommand.AsyncPut:
            all_task = []
            for port in self.connected_ports:
                if not port is exception:
                    all_task.append(create_task(port.__async_send(cmd, False, item, self)))
            await gather(*all_task)
        else:
            raise Exception("Only AsyncPut is supported")


    async def __async_process(self, item, cmd: PortCommand):
        await self.__buffer.put(item)

    def try_get(self):
        return self.__send(PortCommand.TryGet, force_forward=True)


    async def get(self):
        return await self.__buffer.get()

    async def peek(self):
        return await self.__buffer.peek()

    async def put(self, item):
        await self.__async_send(PortCommand.AsyncPut, force_forward=True, item=item)
