import asyncio
import copy
import functools
import json
from json.decoder import JSONDecodeError

import websockets
from websockets.exceptions import *

from networking.connection import PeerConnection

PORT = 11111
IP = 'localhost'
URI = f'ws://{IP}:{PORT}'

loop = asyncio.get_event_loop()


def server(func=None, *, webname=None):
    """A Server decorator. marks the decorated function as a web function,
    which lets the peer class register it as a valid server function for the
    handler

    Args:
        webname (str, optional): The name the command will be called when passed
        over the web. If no name is given, it will use the function's name. It
        is recommended in this case to add undercore ('_') before the name of
        the function as it will automatically sign it as the same command as the
        client equivalent. If no name is given, it will use the function's name.
    """
    if func is None:
        return functools.partial(server, type=type, webname=webname)

    func.server = True

    if webname is None:
        if func.__name__.startswith('_'):
            func.webname = func.__name__[1:]
        else:
            func.webname = func.__name__
    else:
        func.webname = webname

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def client(func=None, *, webname=None):
    """A Client decorator. marks the decorated function as a web function,
    which lets the peer class register it as a valid client function for the
    handler. If no custom webname is giver 

    Args:
        webname (str, optional): The name the command will be called when passed
        over the web.
    """
    if func is None:
        return functools.partial(server, type=type, webname=webname)

    func.client = True
    func.webname = webname if webname else func.__name__

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


class Peer:

    ALL = 0 # Choose all peers
    OUTBOUND = 1 # Chosse only outbound
    INBOUND = 2 # Choose only inbound
    LAST = 3 # Choose last peer (not recommended)
    
    OKAY = 4 # Successfully replied to a get request
    GET = 5 # Get something
    POST = 6 # Post something
    ERROR = 7 # Sent whenever a get reqest has failed

    def __init__(self) -> None:

        # Peers that are connected to us
        self.inbound = set()
        # Peer that we are connected to
        self.outbound = set()

        self.last_conn = None

        self.commands = {}

        methods = []

        cls = type(self)
        # attribute is a string representing the attribute name
        for attribute in dir(cls):
            # Get the attribute value
            attribute_value = getattr(cls, attribute)
            # Check that it is callable
            if callable(attribute_value):
                # Filter all dunder (__ prefix) methods
                if attribute.startswith('__') == False:
                    methods.append(attribute)

        for method in methods:
            try:

                method = getattr(self, method)
                ref = self.commands.get(method.webname)

                if ref is None:
                    ref = [None, None]

                if hasattr(method, 'server'):
                    ref[0] = method

                if hasattr(method, 'client'):
                    ref[1] = method

                self.commands[method.webname] = ref

            except AttributeError:
                pass

    async def init_connection(self, websocket):
        """Initiated whenever a peer wants to connect to us.
        Called by websockets.serve().
        """

        conn = PeerConnection(websocket)
        self.inbound.add(conn)
        # TODO: make sure the connection is working and valid before adding it
        await conn.listener(handler=self.handler)
        self.inbound.remove(conn)

    async def handler(self, data, connection):
        """The default handler function for each message for each connection.
        override if needed.

        Args:
            data (any): the data the was received.
            connection (PeerConnection): The peer connection instance.
        """

        print(f'{connection.str_addr}: received new message {data}')

        try:
            data = json.loads(data)
            
            datatype, data = list(data.values())[0], list(data.values())[1]
            command_name = list(data.values())[0]

            data_temp = copy.deepcopy(data)
            del data_temp['command']
            command_params = data_temp
            command = self.commands[command_name][0]
            
            # TODO: pass paramater as normal arguments instead of one big dictionary
            if datatype == 'get':
                response = await command(command_params)
            if datatype == 'post':
                response = await command(connection, command_params)
            
            print(f'Sending: {response}')
            await connection.send(response)
            
        except JSONDecodeError:
            print(f'{connection.str_addr}: ERROR - not in json format')
            await connection.send(self.pack(Peer.ERROR),
                                  {'message': 'data was sent in wrong format'})
            return

        except AttributeError:
            self.default(data)

    async def connect(self, addr):
        """Connect to a peer

        Args:
            addr (str/(str, int)): The address of the peer we want to connect
            to. can be either a uri or a tuple containing the ip and the port

        Returns:
            _type_: _description_
        """

        # TODO: check if this connection already exits

        if isinstance(addr, tuple):
            uri = f'ws://{addr[0]}:{addr[1]}'
        else:
            uri = addr
        client = await websockets.connect(uri)
        conn = PeerConnection(client, connected=False)
        self.outbound.add(conn)
        self.last_conn = conn

        loop.create_task(conn.listener(handler=self.handler))

    async def disconnect(self, peer_conn):
        """Disconnect from a peer

        Args:
            peer_conn (PeerConnection/int): The peer's connection. enter one of the 
            codes below to easily disonnect from peers:

            0 - Disconnect from all peers
            1 - Disconnect from all outbound peers
            2 - Disconnect from all inbound peers
            3 - Disconnect from last peer
        """

        if isinstance(peer_conn, int):
            match peer_conn:
                case Peer.ALL:
                    for conn in self.inbound:
                        await conn.close()

                    self.inbound = set()

                    for conn in self.outbound:
                        await conn.close()

                    self.outbound = set()

                case Peer.OUTBOUND:
                    for conn in self.outbound:
                        await conn.close()

                    self.outbound = set()

                case Peer.INBOUND:
                    for conn in self.inbound:
                        await conn.close()

                    self.inbound = set()

                case Peer.LAST:
                    return await self.disconnect(self.last_conn)

                case _:
                    return False
        else:
            if peer_conn in self.inbound:
                self.inbound.remove(peer_conn)
                await peer_conn.close()

            elif peer_conn in self.outbound:
                self.outbound.remove(peer_conn)
                await peer_conn.close()

            else:
                return False

        return True

    async def recvall(self, return_when=None, timeout=2):
        """recieves from all connections and blocks the the function untill
        received

        Args:
            return_when (optional): Same as return_when in asyncio.wait().
            defaults to asyncio.FIRST_COMPLETED
            timeout (int, optional): Timeout for the requests. Defaults to 2

        Returns:
            any: The data that was received
        """
        if return_when is None:
            return_when = asyncio.FIRST_COMPLETED

        tasks_full = [(peer, asyncio.create_task(peer.recv()))
                      for peer in self.inbound]

        tasks_full += [(peer, asyncio.create_task(peer.recv()))
                       for peer in self.outbound]

        tasks = [task[1] for task in tasks_full]

        done, pending = await asyncio.wait(tasks, return_when=return_when,
                                           timeout=timeout)

        for task in pending:
            task.cancel()

        if return_when == asyncio.FIRST_COMPLETED:

            # Find the peer that answered first
            for peer in tasks_full:
                if peer[1] in done:
                    return peer[0], json.loads(list(done)[0].result())
        else:
            # Remove tasks that didn't finish
            results = []
            for peer in tasks_full:
                if peer[1] in done:
                    results.append((peer[0], json.loads(peer[1].result())))

            return results

    async def broadcast(self, data, raw=False, wait=False):
        """Broadcasts a message to all known peers

        Args:
            data (any): The data to broadcast
            raw (bool, optional): Whether to keep the data raw or format it in
            json. Defaults to False.
        """

        coros = [peer.send(data, raw) for peer in self.inbound]
        coros += [peer.send(data, raw) for peer in self.outbound]
        await asyncio.gather(*coros)

    def connections(self):
        return len(self.inbound) + len(self.outbound)

    @server
    def default(self, data):
        print(f'No command is found. message: {data}')

    def pack(self, datatype, data):

        match datatype:
            case Peer.OKAY:
                return {'type': 'okay', 'data': data}
            case Peer.GET:
                return {'type': 'get', 'data': data}
            case Peer.POST:
                return {'type': 'post', 'data': data}
            case Peer.ERROR:
                return {'type': 'ERROR', 'data': data}


async def main():

    peer = Peer()
    server = await websockets.serve(peer.init_connection, IP, 11111)
    print(f'Server started. Running on ws://{IP}:11111')

    await peer.connect('ws://localhost:22222')
    await peer.connect('ws://localhost:33333')
    await peer.broadcast('hello', raw=True)
    # await peer.disconnect(3)

    print('Finished')
    await server.wait_closed()


if __name__ == '__main__':

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print('Shutting Down...')
        loop.close()

# Lazy client:
# py -m websockets ws://localhost:22222
