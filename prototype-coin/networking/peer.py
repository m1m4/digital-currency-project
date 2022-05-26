import asyncio
import copy
import functools
import json
from json.decoder import JSONDecodeError

import websockets
from websockets.exceptions import *
from typing import Optional, Union, Tuple, Any, Dict

from .connection import PeerConnection

PORT = 11111
IP = 'localhost'
URI = f'ws://{IP}:{PORT}'


#TODO: rework
def server(func=None, *, webname: Optional[str] = None):
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


def client(func=None, *, webname: Optional[str] = None):
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

    ALL = 0  # Choose all peers
    OUTBOUND = 1  # Chosse only outbound
    INBOUND = 2  # Choose only inbound

    OKAY = 4  # Successfully replied to a get request
    GET = 5  # Get something
    POST = 6  # Post something
    ERROR = 7  # Sent whenever a get reqest has failed

    def __init__(self, port: int = 11111,
                 max_outbound: int = -1,
                 max_inbound: int = -1) -> None:
        """The peer class. Implements a peer that can send and listen to data.
        Uses PeerConnection to handle connections. Data that is sent and 
        received is in a dictionary in JSON format.


        Attributes:
            port (int, optional): The port of the peer. Defaults to 11111.

            inbound (Set[PeerConnection]): A set of connections that are 
            connnected to us. These conncections are client connections.

            outbound (Set[PeerConnection]): A set of connections we are 
            connected to. These are server connections that we can send requests
            to.

            commands (dict): The web commands.

            max_outbound (int, optional): . Defaults to -1.
            max_inbound (int, optional): _description_. Defaults to -1.

            stop(asyncio.Event): Closes node when set


        """

        self.port = port

        self.inbound = set()    # Peers that are connected to us
        self.outbound = set()   # Peers that we are connected to

        self.max_outbound = max_outbound
        self.max_inbound = max_inbound

        self.commands = {}
        self._assign_commands()

        self.stop = asyncio.Event()

    def _assign_commands(self):

        methods = []
        this = type(self)
        # attribute is a string representing the attribute name
        for attribute in dir(this):
            # Get the attribute value
            attribute_value = getattr(this, attribute)
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

            # Doesn't have an attribute of network command
            except AttributeError:
                pass

    async def start(self, *args):
        """Starts the node. Set self.stop to stop the node.

        Args:
            port (int): Which port to open the node in
        """

        async with websockets.serve(self._init_connection, IP, self.port) as server:
            asyncio.create_task(self._init_node(server, *args))
            await self.stop.wait()

            await self.disconnect(Peer.ALL)

    async def _init_node(self, server, *args):
        """The method which runs after the server is up. override to add more
        functionality

        Args:
            server (websocket.WebSocketServer): The server instance
        """
        print(
            f'Server started successfully. listening on ws://{IP}:{self.port}')

    def find_conn(self, ip: int, port: int) -> PeerConnection:

        addr = (ip, port)

        conn = next((conn for conn in self.outbound if conn.addr == addr), None)

        if conn is None:
            conn = next((conn for conn in self.inbound if conn.addr == addr),
                        None)

        return conn

    async def _init_connection(self, websocket):
        """Initiated whenever a peer wants to connect to us.
        Called by websockets.serve().
        """

        conn = PeerConnection(websocket)
        self.inbound.add(conn)
        # TODO: make sure the connection is working and valid before adding it
        await conn.listener(handler=self._handler)
        self.inbound.remove(conn)

    async def _handler(self, data: Any, connection: PeerConnection):
        """The default handler function for each message for each connection.
        data will only be proccessed if it was send in a dictionary in json 
        format

        Args:
            data (Any): The data that was received
            connection (PeerConnection): The connection that we received the 
            data from
        """

        print(f'INFO {connection.str_addr} - Received new message {data}')

        try:
            data = json.loads(data)

            datatype, body = data['type'], data['data']

            # Check if got error
            if datatype == 'error':
                print(
                    f'WARNING {connection.str_addr} - Received error: {body["message"]}')
                return

            command_name = body['command']

            body_temp = copy.deepcopy(body)
            del body_temp['command']
            command_params = body_temp
            command = self.commands[command_name][0]

        except JSONDecodeError:
            print(f'{connection.str_addr}: ERROR - not in json format')
            await connection.send(self.pack(Peer.ERROR,
                                  {'message': 'not in json format'}))
            return

        except KeyError as e:
            print(f'{connection.str_addr}: ERROR - wrong format')
            await connection.send(self.pack(Peer.ERROR,
                                  {'message': 'wrong format'}))
            return

        except TypeError as e:

            if data is None:
                print(f'{connection.str_addr}: INFO - got empty message')

            print(f'{connection.str_addr}: ERROR - {e}')
            await connection.send(self.pack(Peer.ERROR,
                                  {'message': 'data must be a dictionary'}))

        if datatype == 'get':
            response = await command(command_params)
        if datatype == 'post':
            response = await command(connection, command_params)

        if not response is None:
            await connection.send(response)

    async def connect(self, addr: Union[str, Tuple[str, int]]):
        """Connects to a peer

        Args:
            addr (Union[str, Tuple[str, int]): The address of the peer we want to connect
            to. can be either a uri or a tuple containing the ip and the port
        """

        if isinstance(addr, tuple):
            uri = f'ws://{addr[0]}:{addr[1]}'
        else:
            uri = addr

        # Check if this connection already exits
        for node in self.outbound:
            node_uri = f'ws://{node.addr[0]}:{node.addr[1]}'
            if node_uri == uri.replace("localhost", "127.0.0.1"):
                print(f'ERROR - already conncted to {node.str_addr}')
                return

        try:
            client = await websockets.connect(uri)

        except ConnectionRefusedError:
            print(f'ERROR - {uri} refused connection ')
            return

        except InvalidURI:
            print(f'ERROR - "{uri}" is not a valid uri')
            return

        conn = PeerConnection(client, connected=False)
        self.outbound.add(conn)

        return conn

    async def disconnect(self, peer_conn: Union[PeerConnection, int]):
        """Disconnect from a peer

        Args:
            peer_conn (Union[PeerConnection, int]): The peer's connection. enter one of the 
            codes below to easily disonnect from peers:

            Peer.ALL - Disconnect from all peers
            Peer.OUTBOUND - Disconnect from all outbound peers
            Peer.INBOUND - Disconnect from all inbound peers
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

    async def recvall(self, return_when: Optional[str] = None, timeout: int = 3):
        """receives from all connections and blocks the the function untill
        received

        Args:
            return_when (optional): Same as return_when in asyncio.wait().
            defaults to asyncio.FIRST_COMPLETED
            timeout (int, optional): Timeout for the requests. Defaults to 2

        Returns:
            list(PeerConnection, str): A list of tuples with PeerConnection with
            its corresponding answer
        """
        if return_when is None:
            return_when = asyncio.FIRST_COMPLETED

        # tasks_full = [(peer, asyncio.create_task(peer.recv()))
        #               for peer in self.inbound]
        tasks_full = [(peer, asyncio.create_task(peer.recv(timeout=timeout)))
                      for peer in self.outbound]

        # Take only the tasks to pass it to async.wait()
        tasks = [task[1] for task in tasks_full]

        try:
            done, pending = await asyncio.wait(tasks, return_when=return_when,
                                               timeout=timeout)
        except ValueError:
            return

        # Cancel all requests that didn't reponse within the specified timeout
        for task in pending:
            task.cancel()

        if return_when == asyncio.FIRST_COMPLETED:
            # Find the peer that answered first
            for request in tasks_full:
                if request[1] in done:
                    return request[0], request[1].result()
        else:
            results = []
            for request in tasks_full:
                if request[1] in done:
                    results.append((request[0], request[1].result()))

            return results

    async def broadcast(self, data: Any, raw: bool = False, wait: bool = False):
        """Broadcasts a message to all known peers

        Args:
            data (any): The data to broadcast
            raw (bool, optional): Whether to keep the data raw or format it in
            json. Defaults to False.
        """

        coros = [peer.send(data, raw) for peer in self.outbound]
        # coros += [peer.send(data, raw) for peer in self.inbound]
        await asyncio.gather(*coros)

    def connections(self) -> int:
        """Returns the number on online connections

        Returns:
            int: The number of connections
        """
        return len(self.inbound) + len(self.outbound)

    @server
    def default(self, data):
        """The default command to handle incoming messages

        Args:
            data (dict): the data
        """
        print(f'No command is found. message: {data}')

    def pack(self, datatype: int, data: Any) -> dict:
        """Packs the data to be ready to send over the network.

        Args:
            datatype (int): The data type. types are as follows: 
            Peer.OKAY - The request was received correctly. No error occured
            Peer.GET - Request some data and expect a response
            Peer.POST - Broadcast data and not expect a response
            Peer.ERROR - An error has occured

            data (Any): The data to pack

        Returns:
            dict: The data to send
        """

        match datatype:
            case Peer.OKAY:
                return {'type': 'okay', 'data': data}
            case Peer.GET:
                return {'type': 'get', 'data': data}
            case Peer.POST:
                return {'type': 'post', 'data': data}
            case Peer.ERROR:
                return {'type': 'error', 'data': data}


async def main():

    peer = Peer()
    # server = await websockets.serve(peer.init_connection, IP, 11111)
    # print(f'Server started. Running on ws://{IP}:11111')

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
        pass

# Lazy client:
# py -m websockets ws://localhost:22222
