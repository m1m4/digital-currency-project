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
        over the web. If no name is given, it will use the function's name.
    """
    if func is None:
        return functools.partial(server, type=type, webname=webname)
    
    func.server = True
    func.webname = webname if webname else func.__name__
    
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
        over the web. If no name is given, it will use the function's name. It
        is recommended in this case to add undercore ('_') before the name of
        the function as it will automatically sign it as the same command as the
        server equivalent.
    """
    if func is None:
        return functools.partial(server, type=type, webname=webname)
    
    func.client = True
    
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


class Peer:
    
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
    
        print(f'Peer connected: {websocket.remote_address[0]}:{websocket.remote_address[1]}')

        conn = PeerConnection(websocket)
        self.inbound.add(conn)
        await conn.listener(handler=self.handler)
        
        
        self.inbound.remove(conn)
        
    async def handler(self, data, connection):
        """The default handler function for each message for each connection.
        override if needed.

        Args:
            data (any): the data the was received.
            connection (PeerConnection): The peer connection instance.
        """
        
        print(f'{connection.remote_addr[0]}:{connection.remote_addr[1]} received new message: {data}')
        
        try:
            data = json.loads(data)
            
            command_name = list(data.values())[0]
            
            data_temp = copy.deepcopy(data)
            del data_temp['command']
            command_params = data_temp
            command = self.commands[command_name][0]
            
            response = await command(command_params)
            await connection.send(response)
        except JSONDecodeError:
            print(f'{connection.remote_addr[0]}:{connection.remote_addr[1]} -  \
                Invalid data format')
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
        
        #TODO: check if this connection already exits
        
        if isinstance(addr, tuple):
            uri = f'ws://{addr[0]}:{addr[1]}'
        else:
            uri = addr
        client = await websockets.connect(uri)
        conn = PeerConnection(client)
        self.outbound.add(conn)
        
        print(f'Connected succesfully to peer at {uri}')
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
                case 0:
                    for conn in self.inbound:
                        await conn.close()
                    
                    self.inbound = set()
                    
                    for conn in self.outbound:
                        await conn.close()
                    
                    self.outbound = set()
                    
                case 1:
                    for conn in self.outbound:
                        await conn.close()
                    
                    self.outbound = set()
                    
                case 2:
                    for conn in self.inbound:
                        await conn.close()
                    
                    self.inbound = set()
                
                case 3:
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
                      for peer in self.inboud]
        
        tasks_full += [(peer, asyncio.create_task(peer.recv())) 
                       for peer in self.outboud]
        
        tasks = [task[1] for task in tasks_full]
        
        done, pending = await asyncio.wait(tasks, return_when=return_when,
                                           timeout=timeout)
        
        for task in pending:
            task.cancel()
        
        if return_when == asyncio.FIRST_COMPLETED:
            
            # Find the peer that answered first
            for peer in tasks_full:
                if peer[1] in done:
                    return peer[0], list(done)[0].result()
        else:
            # Remove tasks that didn't finish
            results = []
            for peer in tasks_full:
                if peer[1] in done:
                    results.append((peer[0], peer[1].result()))
                    
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
        print(data)

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
# py -m websockets ws://localhost:1234
