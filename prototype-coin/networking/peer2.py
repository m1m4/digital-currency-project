import websockets
import asyncio
from peer import Peer


IP = '127.0.0.1'
loop = asyncio.get_event_loop()

async def main():
    
    peer = Peer()
    server = await websockets.serve(peer.init_connection, IP, 22222)
    print(f'Server started. Running on ws://{IP}:22222')
    
    await server.wait_closed()
    

        

if __name__ == '__main__':
    
    
    try:
        asyncio.run(main())
    
    except KeyboardInterrupt:
        print('Shutting Down...')
        loop.close()