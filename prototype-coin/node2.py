import websockets
import asyncio
from node import Node


IP = '127.0.0.1'
loop = asyncio.get_event_loop()

async def main():
    
    node = Node()
    server = await websockets.serve(node.init_connection, IP, 22222)
    print(f'Server started. Running on ws://{IP}:22222')
    
    await server.wait_closed()
    

        

if __name__ == '__main__':
    
    
    try:
        asyncio.run(main())
    
    except KeyboardInterrupt:
        print('Shutting Down...')
        loop.close()