import asyncio
import hashlib
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Any

from block import Block, Transaction
import treenode as tree
from blockchain import Blockchain
from wallet import Wallet


class Miner:
    def __init__(self, miner_addr: str, max_txns: int = 100):

        self.max_txns = max_txns    # Max transaction to insert to each block
        self.mempool = []   # Memory pool. holds pending transactions

        self.miner_addr = miner_addr

        self.stop = asyncio.Event() # Stops mining when set

    def add_txn(self, txn: Transaction):
        """Adds a transaction to the memory pool. will not add duplicate 
        transactions

        Args:
            txn (Transaction): The transaction.
        """
        # TODO: add transaction in index by mining fee (max_txns[0] should have
        # the hightest fee)

        if not txn in self.mempool:
            self.mempool.append(txn)

    def _find_hash(self, data: str, difficulty: int, offset: int, found_event: mp.Event):
        
        """Finds the hash for a block with given difficulty. Should be used in a
        multiprocessing pool.

        Args:
            data (str): The base data (or Block)
            
            difficulty (int): The difficulty of the block
            
            offset (int): Used when multiple processes are mining. Every
            process should have a different offeset. Offsets for each process
            should look like this when n is the number of cores the cpu have:
            0,1,2,...,n-1.
             
            found_event (multiproccessing.Event): Pass to tell the other cores
            to stop whenever one of them has found the hash

        Returns:
            Tuple[str, str]: Returns the hash it found and the proof
        """

        # print(f'PID {mp.current_process().pid}: Searching for hash')

        skip = mp.cpu_count()
        data = str(data)
        proof = 0 + offset

        while True:

            if found_event.is_set():
                # print(f'PID {mp.current_process().pid}: Cancelled')
                return

            data_hash = hashlib.sha256(
                (data + str(proof)).encode()).hexdigest()

            diff_string = '0' * difficulty
            if data_hash.startswith(diff_string):
                return data_hash, str(proof)
            else:
                proof += skip
        # TODO: Start mining a new block if a new block is received

    async def mine(self, blockchain: Blockchain, handler: Callable[[Block], Any]):
        """Starts mining blocks and calls handler(block) whenever a new block is
        mined. To stop mining, set self.stop.

        Args:
            blockchain (Blockchain): The blockchain to work on mining. 
            Automatically choose the best chain to work on.
            
            handler (Callable[[Block], Any]): Called when a new block is mined
        """

        # Don't mine if theres no address to mine to
        if self.miner_addr is None:
            return
        
        loop = asyncio.get_running_loop()

        while True:
            if self.stop.is_set():

                print('MINER - Stopped mining')
                handler.cancel()
                return
            
            txns = []
            for _ in range(self.max_txns):
                try:
                    txns.append(self.mempool.pop(0))

                except IndexError:
                    break   # No transactions left in mempool

            # Add Block reward
            txns.append(Transaction('0.1', 'mine', [self.miner_addr, 10],
                                    None, None))

            if blockchain.unconfirmed.data is None:
                last_hash = blockchain.chain[-1]._hash
            else:
                potential_blocks = tree.get_end_children(
                    blockchain.unconfirmed)
                last_hash = max(potential_blocks,
                                key=lambda x: x.get_level()).data._hash

            timestamp = str(time.time())

            difficulty = blockchain.difficulty
            block_data = f'{timestamp}{last_hash}{txns}'

            # Run all proccesses in the computer to find hash
            with ProcessPoolExecutor() as pool, mp.Manager() as manager:

                finished = manager.Event()

                workers = [loop.run_in_executor(pool, self._find_hash,
                                                block_data,
                                                difficulty,
                                                i,
                                                finished)
                           for i in range(mp.cpu_count())]

                done, pending = await asyncio.wait(workers,
                                                   return_when=
                                                   asyncio.FIRST_COMPLETED)

                for worker in workers:
                    if worker in done:
                        try:
                            block_hash, proof = worker.result()

                        except (FileNotFoundError, EOFError, BrokenPipeError) as e:
                            print(f'ERROR - {e}')

                        finished.set()

                        block = Block(last_hash=last_hash,
                                           txns=txns,
                                           proof=proof,
                                           timestamp=timestamp,
                                           _hash=block_hash)

                        print(f'MINER - Block created with hash {block_hash}')
                        await handler(block)

                    if worker in pending:
                        worker.cancel()
                        

async def main():
    blockchain = Blockchain()
    wallet = Wallet()

    miner = Miner(wallet.addr)
    await miner.mine(blockchain=blockchain, handler=handler)


if __name__ == "__main__":
    asyncio.run(main())
