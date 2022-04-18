import re
from xmlrpc.client import FastUnmarshaller
import websockets
import asyncio
import websockets.exceptions


PORT = 11111
IP = 'localhost'
URI = f'ws://{IP}:{PORT}'

loop = asyncio.get_event_loop()

class Peer:
    
    def __init__(self) -> None:
        
        # Peers that are connected to us
        self.inbound = set()
        # Peer that we are connected to
        self.outbound = set() 
        
        self.last_conn = None
        
    async def handler(self, websocket):
        """Initiated whenever a peer wants to connect to us.
        Called by websockets.serve().
        """
    
        print(f'Peer connected: {websocket.remote_address[0]}:{websocket.remote_address[1]}')

        conn = PeerConnection(websocket)
        self.inbound.add(conn)
        await conn.listener()
        
        
        self.inbound.remove(conn)
        
    
    
    async def connect(self, addr):
        """Connect to a peer

        Args:
            addr (str/(str, int)): The address of the peer we want to connect
            to. can be either a uri or a tuple containing the ip and the port

        Returns:
            _type_: _description_
        """
        
        
        if isinstance(addr, tuple):
            uri = f'ws://{addr[0]}:{addr[1]}'
        else:
            uri = addr
        client = await websockets.connect(uri)
        conn = PeerConnection(client)
        self.outbound.add(conn)
        
        print(f'Connected succesfully to peer at {uri}')
        self.last_conn = conn
        
        loop.create_task(conn.listener())

        
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
    
    
    async def broadcast(self, data, raw=False):
        """Broadcasts a message to all known peers

        Args:
            data (any): The data to broadcast
            raw (bool, optional): Whether to keep the data raw or format it in
            json. Defaults to False.
        """
        
        for peer in self.inbound:
            peer.send(data, raw)

        for peer in self.outbound:
            peer.send(data, raw)
        



class PeerConnection():
    
    def __init__(self, websocket):
        
        self.websocket = websocket
        self.remote_addr = websocket.remote_address
        self.local_addr = websocket.local_address
        
    async def listener(self):
        """A listener that listens to all incoming data from this connection
        """
        
        async for message in self.websocket:
            print(message)
            
        await self.close()
        print(f'Disconnected from {self.remote_addr[0]}:{self.remote_addr[1]}')
            
    
    async def send(self, data, raw=False):
        """Sends a message to the other end of this connection.

        Args:
            data (any): The data to send
            raw (bool, optional): Whether to keep the data raw or format it in
            json. Defaults to False.
        """
        
        if raw: 
            await self.websocket.send(data)
        else:
            pass
    
    async def recv(self, raw=False):
        """Recieves data from the other end of this connection.

        Args:
            raw (bool, optional): Whether to exepect the data as json.
            Defaults to False.

        Returns:
            any: The data
        """
        if raw: 
            return await self.websocket.recv()
        else:
            pass
    
    async def close(self):
        """Closes this connection.
        """
        await self.websocket.close()
        

async def main():
    
    peer = Peer()
    server = await websockets.serve(peer.handler, IP, PORT)
    print(f'Server started. Running on {URI}')
    
    # client = await websockets.connect('ws://localhost:22222')
    # await client.send('hello world')
    # await client.recv() 
    await server.wait_closed()
        

if __name__ == '__main__':
    
    asyncio.run(main())
    
# Lazy client: 
# py -m websockets ws://localhost:1234

