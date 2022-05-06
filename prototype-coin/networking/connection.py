import asyncio
import functools
import json

import websockets
from websockets.exceptions import *

#TODO: maybe convert to child class of websocket?
class PeerConnection():
    
    def __init__(self, websocket, connected=True):
        """Initializes the PeerConnection class

        Args:
            websocket (_type_): _description_
            connected (bool, optional): Helps indicates if were the ones that
            initialized the connection or a new peer tried to connect to us.
            Defaults to True.
        """
        
        self.websocket = websocket
        self.str_addr = f'{websocket.remote_address[0]}:{websocket.remote_address[1]}'
        self.addr = websocket.remote_address
        
        if connected:
            print(f'Peer connected - {self.str_addr}')
        else:
            print(f'Connnected to peer: {self.str_addr}')
        
    async def listener(self, handler=None):
        """A listener that listens to all incoming data from this connection

        Args:
            handler (function(data, connection), optional): The handler function that will run 
            whenever a new message is received from this conncetion. handler
            function is passed, the data that was received will be printed.
            handler function args:
                data (any): the data the was received
                connection (PeerConnection): This connection
        """
        try:
            async for message in self.websocket:
                
                if handler is None:
                    print(message)
                else:
                    await handler(message, self)
            
            await self.close()
        
        except ConnectionClosedError:
            await self.close()
        
        finally:
            print(f'Disconnected from {self.str_addr}')
                    
    
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
            await self.websocket.send(json.dumps(data))
    
    async def recv(self, timeout=2):
        """Recieves data from the other end of this connection. Used to block an
        asynchronous function until a reply is recieved.

        Returns:
            any: The data
        """
        try:
            return await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
        except ConnectionClosedError:
            await self.close()
            return

        except asyncio.TimeoutError:
            await self.close()
            return
    
    async def close(self):
        """Closes this connection.
        """
        await self.websocket.close()
    
    @functools.cached_property
    def json(self):
        new_dict = {'websocket': self.websocket.__dict__, 'str_addr': self.str_addr}
        return json.dumps(new_dict)
    
    
    
