import asyncio
import json

import websockets
from websockets.exceptions import *


class PeerConnection():
    
    def __init__(self, websocket):
        
        self.websocket = websocket
        self.remote_addr = websocket.remote_address
        self.local_addr = websocket.local_address
        
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
