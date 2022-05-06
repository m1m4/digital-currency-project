import asyncio
import json
import websockets

from blockchain import Blockchain
from networking.peer import Peer, client, server
from wallet import Wallet

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
            
    async def request(self, data, broadcast=True, conn=None):
        
        if broadcast:
            await self.broadcast(data)
            results = await self.recvall(asyncio.ALL_COMPLETED)
        else:
            if conn is None:
                raise TypeError("request() missing 1 required argument when broadcast=True: 'conn'")
            await conn.send()
            results = await conn.recv()

        return results
            
    def post_block(self):
        pass
    
    def post_txn(self):
        pass
    
    
    @client
    async def _get_block(self, block_hash=None, height=None):
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
        
        response = await self.request(request)
        
        #TODO: fetch results and check validity of blocks  
        return response
        
    
    @client
    async def _get_blocks(self, hashes=None, start_height=None, end_height=None):
        """Requests blocks from the blockchain from all connected peers. If no
        identifier is given, it will ask for all blocks.

        Args:
            hashes (list, optional): List of hashes for the requested blocks.
            start_height (str/int, optional): Starting height for the blocks
            start_height (str/int, optional): End height for the blocks
        """
        
        request = {'command': self.get_block.webname}
        
        if not hashes is None:
            request['hashes'] = hashes
        else:
            if not start_height is None:
                request['start_height'] = start_height
            if not end_height is None:
                request['start_height'] = start_height
        
        
        #TODO: fetch results and check validity of blocks 
        response = await self.request(request)
        return response
    
    @client
    async def _get_nodes(self):
        response = await self.request({'command': self._get_nodes.webname})

        #TODO: connect to the new nodes
        return response
    
    @client
    async def _get_height(self):
        
        return await self.request({'command': self._get_height.webname})
    
    @client
    async def _get_hash(self, height):
        
        return await self.request({'command': self._get_hash.webname,
                   'height': height})
    
    @client
    async def _get_addr(self, conn):
        return await self.request({'command': self._get_height.webname},
                            broadcast=False, conn=conn)
    
    @server
    async def get_block(self, params):
        
        block_hash = params.get('block_hash')
        height = params.get('height')
        
        if not block_hash is None:
            block = self.blockchain.get_block(block_hash)
            
            if block is None:
                block = 'not found'
        
        elif not height is None:
            block = self.blockchain.chain[height - 1]
            
        else:
            block = self.blockchain.last_block()
            
        return {'response': block.json()}
    
    @server
    async def get_blocks(self, params):
        
        hashes = params.get("hashes")
        start_height = params.get("start_height")
        end_height = params.get("end_height")
        
        blocks = []
        if not hashes is None:    
            
            for _hash in hashes:
                block = self.blockchain.get_block(_hash)
                if not block is None:
                    blocks.append(block.json())
                    
        else:
            if start_height is None:
                start_height = 1
            
            if end_height is None:
                end_height = self.blockchain.height()
                
            temp_blocks = self.blockchain.chain[start_height - 1:end_height]
            blocks = [block.json() for block in temp_blocks]
            
        return {'response': blocks}
    
    @server
    async def get_nodes(self, params):
        
        conns_inbound = [conn.addr for conn in self.inbound]
        conns_outbound = [conn.addr for conn in self.outbound]
        
        return {'response': {'inbound': conns_inbound,
                             'outbound': conns_outbound}}
    
    @server
    async def get_height(self, params):
        
        unconfirmed = params.get('unconfirmed')
        
        if unconfirmed is None:
            unconfirmed = False
        
        return {'response': self.blockchain.height(unconfirmed=unconfirmed)}
    
    @server
    async def get_hash(self, params):
        
        height = params.get('height')
        
        if not height is None:
            _hash = self.blockchain.chain(height - 1)._hash
        else:
            _hash = self.blockchain.last_block()._hash
            
        return {'response': _hash}
             
    @server
    async def get_addr(self, params):
        
        return {'response': self.wallet.addr}
    
    
async def main():
    
    IP = '127.0.0.1'
    node = Node()
    server = await websockets.serve(node.init_connection, IP, 11111)
    print(f'Server started. Running on ws://{IP}:11111')
    
    await node.connect('ws://localhost:22222')
    # await node.connect('ws://localhost:33333')
    print('Requesting last block... ')
    response = await node._get_block()
    print(response)
    # await peer.disconnect(3)
    
    await server.wait_closed()
    

        

if __name__ == '__main__':
    
    
    try:
        asyncio.run(main())
    
    except KeyboardInterrupt:
        print('Shutting Down...')
        loop.close()
    
    
    
    
    