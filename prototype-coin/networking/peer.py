import asyncio
import copy
import functools
import json
import logging
from json.decoder import JSONDecodeError

import websockets
from websockets.exceptions import *

from networking.connection import PeerConnection

PORT = 11111
IP = 'localhost'
URI = f'ws://{IP}:{PORT}'

loop = asyncio.get_event_loop()

def server(func=None, *, webname=None):
    
    if func is None:
        return functools.partial(server, type=type, webname=webname)
    
    func.server = True
    func.webname = webname if webname else func.__name__
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    return wrapper

def client(func=None, *, webname=None):
    
    if func is None:
        return functools.partial(server, type=type, webname=webname)
    
    func.client = True
    func.webname = webname if webname else func.__name__
    
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
        # attribute is a string representing the attribute name
        for attribute in dir(Peer):
            # Get the attribute value
            attribute_value = getattr(Peer, attribute)
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
        
        logging.info(f'{connection.remote_addr[0]}:{connection.remote_addr[1]} received new message: {data}')
        
        try:
            data = json.loads(data)
            
            command_name = list(data.values())[0]
            
            data_temp = copy.deepcopy(data)
            del data_temp['command']
            command_params = data_temp
            command = getattr(self, command_name)
            
            response = await asyncio.gather(command(command_params))
            await connection.send(list(response)[0].result())
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
