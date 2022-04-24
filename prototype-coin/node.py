import asyncio
import logging

import websockets

from blockchain import Blockchain
from networking.peer import Peer, client, server
from wallet import Wallet

logging.basicConfig(level=logging.WARNING, format='%(levelname)%s %(message)%s')
loop = asyncio.get_event_loop()

class Node(Peer):
    
    
    def __init__(self, blockchain=None, wallet=None) -> None:
        super().__init__()
        
        if blockchain is None:
            self.blockchain = Blockchain()
        else:
            self.blockchain = blockchain
            
        if wallet is None:
            self.wallet = Wallet()
        else:
            self.wallet = wallet
            
    def post_block(self):
        pass
    
    def post_txn(self):
        pass
    
    
    @client
    async def get_block(self, block_hash=None, height=None):
        """Requests a block from the blockchain from all connected peers. There
        must be at least 1 argument that identifies the block

        Args:
            block_hash (str, optional): The block's hash.
            height (str/int, optional): The block's height in the blockchain.
            not recommended since every Node might send a different block.
        """
        
        request = {'command': self.get_block.webname}
        
        if not block_hash is None:
            request['block_hash'] = block_hash
            
        elif not block_hash is None:
            request['height'] = height
            
        else:
            logging.warning('get_block function was called without arguments.')
            return
        
        await self.broadcast(request)
        
        
        #TODO: check validity of blocks
        tasks = [asyncio.create_task(peer.recv()) for peer in self.inbound]
        tasks += [asyncio.create_task(peer.recv()) for peer in self.outbound]
        
        done, pending = await asyncio.wait(tasks,
                                            return_when=asyncio.FIRST_COMPLETED)
        
        for task in pending:
            task.cancel()
        
        return list(done)[0].result()
        
        
    
    @client
    def get_blocks(self, *hashes):
        pass
    
    @client
    def get_nodes(self):
        pass
    
    @client
    def get_height(self):
        pass
    
    @client
    def get_hash(self, height):
        pass
    
    
    @server
    def recv_block(self, params):
        
        #TODO: add height support
        
        
        block_hash = params.get('block_hash')
        
        if block_hash is None:
            logging.info('recv_block: got wrong parameters')
            return
            #TODO: Create error codes
        
        block = self.blockchain.get_block(block_hash)
        
        if block is None:
            block = 'not found'
            
        return {'response': block}
    
    @server
    def recv_blocks(self):
        pass
    
    @server
    def recv_nodes(self):
        pass
    
    @server
    def recv_height(self):
        pass
    
    @server
    def recv_hash(self):
        pass
    
    
    
async def main():
    
    IP = '127.0.0.1'
    node = Node()
    server = await websockets.serve(node.init_connection, IP, 11111)
    print(f'Server started. Running on ws://{IP}:11111')
    
    await node.connect('ws://localhost:22222')
    # await node.connect('ws://localhost:33333')
    response = await node.get_block(block_hash='123456')
    print(response)
    # await peer.disconnect(3)
    
    await server.wait_closed()
    

        

if __name__ == '__main__':
    
    
    try:
        asyncio.run(main())
    
    except KeyboardInterrupt:
        print('Shutting Down...')
        loop.close()
    
    
    
    
    