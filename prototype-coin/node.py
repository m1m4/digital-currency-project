import asyncio
import json
from urllib import response

import websockets

import block as blk
from blockchain import Blockchain
from networking.peer import Peer, client, server
from wallet import Wallet

#TODO: replace get_event_loop()
loop = asyncio.get_event_loop()


class Node(Peer):

    ALL = 0
    SINGLE = 1

    def __init__(self, blockchain=None, wallet=None, miner=None) -> None:
        super().__init__()

        if blockchain is None:
            self.blockchain = Blockchain()
        else:
            self.blockchain = blockchain

        if wallet is None:
            self.wallet = Wallet()
        else:
            self.wallet = wallet

        self.miner = miner


        self.received = []  # Stuff received from the network
        # print(self.commands)
        
    
    async def start(self, port):
        await super().start(port)
        
        # # Connect to as much connections as possible
        # self.scan_network()
        
        # #TODO: Check last few hashed and get the most trustworthy nodes
        # #TODO: Split block requests to disperse network pressure
        
        heights = self.get_height()
        
        max_peer = max(heights, key=lambda x:x[1])
        max_peer = 
        
        

    async def request(self, data, broadcast=None, conn=None):
        
        if broadcast is None:
            broadcast = Node.ALL

        match broadcast:
            case Node.ALL:
                await self.broadcast(self.pack(Node.GET, data))
                results = await self.recvall(asyncio.ALL_COMPLETED)

            case Node.SINGLE:
                if conn is None:
                    raise TypeError(
                        "request() missing 1 required argument when broadcast=True: 'conn'")
                await conn.send()
                results = await conn.recv()

        return results

    @client
    async def post_block(self, block):
        """Send the hash to all known peers. Since a block might be big (>1mb)
        we send its hash instead of all the block to let other know we have that
        block.

        Args:
            block (Block): The block.
        """
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

            response = await self.get_block(block_hash, mode=Node.SINGLE, conn=server_conn)
            response_dict = json.loads(response)
            if response_dict['type'] != 'okay':
                print(f'WARNING - did not get reqested block. message:\
{response}')
                return
            
            block_dict = response_dict['data']['block']
            block = blk.from_dict(block_dict)
            
            print(f'INFO {conn.str_addr} - Got block with hash {block._hash}')
            self.blockchain.add_block(block)
            
            # TODO: have a list of known blocks
            # await self.post_block(block)
        
        else: 
            print(f'INFO {conn.str_addr} - Got existing block')



    @client
    async def post_txn(self, txn):
        data = self.pack(Node.POST,
                         {'command': 'post_txn', 'txn': dict(txn._asdict())})
        await self.broadcast(data)

    @server
    async def _post_txn(self, conn, params):
        
        #TODO: have a list of known txns
        if self.miner is None:
            print(f'INFO {conn.str_addr} - Got transaction')
            # await self.post_txn(txn)
        else:
            raise NotImplementedError('mempool not implemented yet.')

    @client
    async def get_block(self, block_hash=None, height=None, mode=None, conn=None):
        """Requests a block from the blockchain from all connected peers. There
        must be at least 1 argument that identifies the block

        Args:
            block_hash (str, optional): The block's hash.
            height (str/int, optional): The block's height in the blockchain.
            not recommended since every Node might send a different block.
        """

        if mode is None:
            mode = Node.ALL

        request = {'command': self.get_block.webname}

        if not block_hash is None:
            request['block_hash'] = block_hash
        elif not block_hash is None:
            request['height'] = height

        if mode == Node.ALL:
            response = await self.request(request)
        elif mode == Node.SINGLE:
            await conn.send(self.pack(Node.GET, request))
            response = await conn.recv()

        # TODO: fetch results and check validity of blocks
        return response

    @client
    async def get_blocks(self, hashes=None, start_height=None, end_height=None):
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

        # TODO: fetch results and check validity of blocks
        response = await self.request(request)
        return response

    @client
    async def get_nodes(self):
        response = await self.request({'command': self._get_nodes.webname})

        # TODO: connect to the new nodes
        return response

    @client
    async def get_height(self):

        responses = await self.request({'command': self._get_height.webname})
    
        # Remove all the message wrappers and return only the list of the peers 
        # with the height
        response_new = []
        for response in responses:
            try:
                response_new.append((response[0], response[1]['data']['height']))
            except KeyError:
                continue
        
        return response_new

    @client
    async def get_hash(self, height):

        return await self.request({'command': self._get_hash.webname,
                                   'height': height})

    @client
    async def get_addr(self, conn):
        return await self.request({'command': self._get_height.webname},
                                  broadcast=False, conn=conn)

    @server
    async def _get_block(self, params):

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

    @server
    async def _get_addr(self, params):

        return self.pack(Node.OKAY, {'address': self.wallet.addr})


async def main():

    # IP = '127.0.0.1'
    node = Node()
    # server = await websockets.serve(node.init_connection, IP, 11111)
    # print(f'Server started. Running on ws://{IP}:11111')
    
    await node.start(port=11111)

    await node.connect('ws://localhost:22222')
    # await node.connect('ws://localhost:33333')
    # print('Posting block... ')
    height = await node.get_height()
    print(height)
    # print('Posting new Trasaction...')
    # node.wallet.debug_generate_outputs(10, 1)
    # txn = node.wallet.send(0, ('mima', 10))
    
    # await node.post_txn(txn)
    # await peer.disconnect(3)

    await node._server.wait_closed()


if __name__ == '__main__':

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print('Shutting Down...')
        loop.close()
