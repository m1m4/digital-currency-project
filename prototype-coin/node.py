import asyncio
from typing import Optional

import block as blk
from blockchain import Blockchain
from miner import Miner
from networking import Peer, client, server
from wallet import Wallet

class Node(Peer):

    ALL = 0
    SINGLE = 1

    #TODO: choose port number for all nodes
    def __init__(self, port: Optional[int]=11111,
                 max_outbound: int=-1,
                 max_inbound: int=-1,
                 blockchain: Optional[Blockchain]=None,
                 blockchain_dir: Optional[str]=None,
                 miner: Optional[Miner]=None):
        
        super().__init__(port=port,
                         max_outbound=max_outbound,
                         max_inbound=max_inbound)

        if blockchain is None:
            self.blockchain = Blockchain(data_dir=blockchain_dir)
        else:
            self.blockchain = blockchain

        self.miner = miner

        # Stuff received from the network
        self.recent_txns = []
        self.recent_blocks = []

    async def _init_node(self, server, *addrs):
        # TODO: Check last few hashed and get the most trustworthy nodes
        # TODO: Split block requests to disperse network pressure
        
        await super()._init_node(server)
        
        # Connect to as much connections as possible
        # self.scan_network()
        
        for addr in addrs:
            await self.connect(addr)
        
        print('INFO - Loading the blockchain from disk...')
        
        try:
            result = self.blockchain.load()
            
            # If not new blocks were added, download the blockchain
            if not result:
                raise FileNotFoundError
            
        except FileNotFoundError:
            print('WARNING - No blockchain is found at the set location. Downloading blockchain from the web')
            
            try:
                heights = await self.get_height()
                max_peer = max(heights, key=lambda x: x[1])[0]
                response = await self.get_blocks(mode=Node.SINGLE, conn=max_peer)
                blocks = response[0][1]
                self.blockchain.add_blocks(blocks, update_file=False)

            except ValueError as e:
                print('WARNING - Not connected to any nodes')
            
        # Create the blockchain on disk after the blocks were downloaded
        self.blockchain.save()
        # Run the miner module if added to the node
        if not self.miner is None:
            await self.miner.mine(blockchain=self.blockchain, handler=self.handle_block)

    async def handle_block(self, block):
        """ Process newly mined blocks. This method is invoked whenever a block
        is mined.
        """
        self.blockchain.add_block(block, update_file=True)
        await self.post_block(block)
                

    async def request(self, data, mode=None, conn=None):

        if mode is None:
            mode = Node.ALL

        match mode:
            case Node.ALL:
                await self.broadcast(self.pack(Node.GET, data))
                results = await self.recvall(asyncio.ALL_COMPLETED)
                if results is None:
                    return []

            case Node.SINGLE:
                if conn is None:
                    raise TypeError(
                        "request() 'conn' argument is required when mode=Node.SINGLE")
                await conn.send(self.pack(Node.GET, data))
                results = [(conn, await conn.recv())]

        return results

    @client
    async def post_block(self, block: blk.Block):
        """Send the hash to all known peers. Since a block might be big (>1mb)
        we send its hash instead of all the block to let other know we have that
        block.

        Args:
            block (Block): The block.
        """
        print(f'INFO - Posting block')

        data = self.pack(Node.POST,
                         {'command': 'post_block', 'hash': block._hash})
        await self.broadcast(data)

    @server
    async def _post_block(self, conn, params):
        """Checks if we have that block in out blockchain, if not we will send a
        request for that block

        Args:
            params (_type_): _description_
        """
        block_hash = params.get('hash')

        if block_hash is None:
            print(f'INFO {conn.str_addr} - Didnt receive hash for post_block')

        if self.blockchain.get_block(block_hash) is None:

            # TODO: change port here
            server_conn = await self.connect((conn.addr[0], 11111))
            
            # If we already made connection with that computer
            if server_conn is None:
                server_conn = self.find_conn(conn.addr[0], 11111)

            response = await self.get_block(block_hash, mode=Node.SINGLE, conn=server_conn)
            
            #TODO: choose the most common block
            if response:
                block = response[0][1]
            else:
                print(f'WARNING - did not get reqested block. response: {response}')
                return
            
            print(f'INFO {conn.str_addr} - Got block with hash {block._hash}')
            self.blockchain.add_block(block, update_file=True)

            if not block._hash in self.recent_blocks:
                self.recent_blocks.append(block._hash)
                await self.post_block(block)

        else:
            print(f'INFO {conn.str_addr} - Got existing block')

    @client
    async def post_txn(self, txn: blk.Transaction):

        print('INFO - Posting transaction')

        if not self.miner is None:
            self.miner.add_txn(txn)

        data = self.pack(Node.POST,
                         {'command': 'post_txn', 'txn': dict(txn._asdict())})

        await self.broadcast(data)

    @server
    async def _post_txn(self, conn, params):

        print(f'INFO {conn.str_addr} - Got transaction')

        txn_dict = params.get('txn')
        
        txn = blk.to_txn(txn_dict)

        # TODO: replace transactions with their hash
        if not txn in self.recent_txns:
            self.recent_txns.append(txn)
            await self.post_txn(txn)

    @client
    async def get_block(self, block_hash=None,
                        height=None,
                        mode=None,
                        conn=None):
        """Requests a block from the blockchain from all connected peers. There
        must be at least 1 argument that identifies the block

        Args:
            block_hash (str, optional): The block's hash.
            height (str/int, optional): The block's height in the blockchain.
            not recommended since every Node might send a different block.
            mode (int): The mode of get_block. Node.ALL broadcasts while
            Node.SINGLE sends only to 1 node. Defaults to Node.ALL
            conn (Peer): The peer/node to send to. Raises TypeError when mode is
            Node.SINGLE and conn is none
        """

        if conn is None:
            print(f'INFO - Requesting block')
        else:
            print(f'INFO {conn.str_addr} - Requesting block')

        if mode is None:
            mode = Node.ALL

        request = {'command': self.get_block.webname}

        if not block_hash is None:
            request['block_hash'] = block_hash
        elif not block_hash is None:
            request['height'] = height

        try:
            response = await self.request(request, mode=mode, conn=conn)
        except TypeError:
            print('ERROR - mode is Node.SINGLE but no peer object was passed')
            return
        
        response_final = [(r[0], blk.to_block(r[1]['data']['block']))
                            for r in response]
        
        return response_final

        # TODO: fetch results and check validity of blocks

    @client
    async def get_blocks(self, hashes=None,
                         start_height=None,
                         end_height=None,
                         mode=None,
                         conn=None):
        """Requests blocks from the blockchain from all connected peers. If no
        identifier is given, it will ask for all blocks.

        Args:
            hashes (list, optional): List of hashes for the requested blocks.
            start_height (str/int, optional): Starting height for the blocks
            start_height (str/int, optional): End height for the blocks
        """

        if conn is None:
            print(f'INFO - Requesting blocks')
        else:
            print(f'INFO {conn.str_addr} - Requesting blocks')

        if mode is None:
            mode = Node.ALL

        request = {'command': self.get_blocks.webname}

        if not hashes is None:
            request['hashes'] = hashes
        else:
            if not start_height is None:
                request['start_height'] = start_height
            if not end_height is None:
                request['end_height'] = end_height

        # TODO: fetch results and check validity of blocks
        try:
            #TODO: return responses that returned an error
            response = await self.request(request, mode=mode, conn=conn)
            response_final = [(r[0], [blk.to_block(block)
                                      for block in r[1]['data']['blocks']])
                              for r in response]
        except TypeError as e:
            print(f'ERROR - {e}')
            return

        return response_final

    @client
    async def get_nodes(self):

        print(f'INFO - Requesting nodes')

        response = await self.request({'command': self._get_nodes.webname})

        # TODO: connect to the new nodes
        return response

    @client
    async def get_height(self):

        print(f'INFO - Requesting height')

        responses = await self.request({'command': self._get_height.webname})

        # Remove all the message wrappers and return only the list of the peers
        # with the height
        response_new = []
        for response in responses:
            try:
                response_new.append(
                    (response[0], response[1]['data']['height']))
            except KeyError:
                continue

        return response_new

    @client
    async def get_hash(self, height):

        print(f'INFO - Requesting hash of height {height}')

        return await self.request({'command': self._get_hash.webname,
                                   'height': height})

    # @client
    # async def get_addr(self, conn):

    #     print(f'INFO {conn.str_addr} - Requesting wallet address')

    #     return await self.request({'command': self._get_height.webname},
    #                               mode=False, conn=conn)

    @server
    async def _get_block(self, params):

        block_hash = params.get('block_hash')
        height = params.get('height')

        if not block_hash is None:
            block = self.blockchain.get_block(block_hash)

            # TODO: replace with an error response
            if block is None:
                return self.pack(Node.ERROR, {'message': 'block not found'})

        elif not height is None:
            block = self.blockchain.chain[height - 1]

        else:
            block = self.blockchain.last_block()

        return self.pack(Node.OKAY, {'block': block.json()})

    @server
    async def _get_blocks(self, params):

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

        return self.pack(Node.OKAY, {'blocks': blocks})

    @server
    async def _get_nodes(self, params):
        """Returns to the client all the outbound connection addresses they 
        have. Does not get the inbound connections since they and will not
        answer requests.

        Args:
            params (dict): the parameters of this command. Serves no use

        Returns:
            _type_: The connections packed as a dictionary with okay message
        """

        conns_outbound = [conn.addr for conn in self.outbound]

        return self.pack(Node.OKAY,
                         {'outbound': conns_outbound})

    @server
    async def _get_height(self, params):

        unconfirmed = params.get('unconfirmed')

        if unconfirmed is None:
            unconfirmed = False

        return self.pack(Node.OKAY, {'height': self.blockchain.height(unconfirmed=unconfirmed)})

    @server
    async def _get_hash(self, params):

        height = params.get('height')

        if not height is None:
            _hash = self.blockchain.chain(height - 1)._hash
        else:
            _hash = self.blockchain.last_block()._hash

        return self.pack(Node.OKAY, {'hash': _hash})

    # @server
    # async def _get_addr(self, params):

    #     return self.pack(Node.OKAY, {'address': self.wallet.addr})


async def main():
    
    
    wallet = Wallet()
    miner = Miner(wallet.addr)
    node = Node(port=11111, miner=miner)
    await node.start('ws://localhost:22222')

    
if __name__ == '__main__':
    
    asyncio.run(main())
        
    
            
        
    
        

    
