import Block
from Block import Constants
import os
import json
from types import SimpleNamespace


class Blockchain:

    def __init__(self, chain=None, dir=None):
        """A class that represents the blockchain. It is responsible to manage
        the blockchain.
        
        Args:
            chain (dict, optional): The blockchain. Defaults to Only genesis
            block.
            
            dir (str, optional): the file directory. Defaults to this file path.
        """
        if chain is None:
            self.chain = {1: Constants.GENESIS}
        else:
            self.chain = chain

        # Optional custom directory
        if dir is None:
            self.dir = os.path.dirname(os.path.realpath(__file__))
        else:
            self.dir = dir

    def add_block(self, txns, pow):
        """Adds a new Block to the blockchain

        Args:
            txns (tuple): a tuple of all the transaction in the block
            
            pow (str): the proof of work of the block

        Returns:
            Block: the newly created block that was added to the blockchain
        """
        last_block = list(self.chain.values())[-1]

        new_block = Block.Block(last_block.hash, data, pow)
        self.chain.update({len(self.chain) + 1: new_block})

        return new_block

    def print_blocks(self, start=1, end=None):
        """Prints the blockchain to console. Use only when blockchain is very
        small

        Args:
            start (int, optional): start block index. Defaults to 1.
            
            end ([type], optional): end block index. Defaults to the last block.
        """
        if end is None:
            end = len(self.chain)

        for id in self.chain:
            if start <= id <= end:
                print(f'Block #{id}:\n' + str(self.chain.get(id)))

    def save(self):
        """Saves the blockchain to a json file
        """

        with open(self.dir + r'\blockchain.json', 'w', encoding='utf-8') as file:
            json.dump(self.chain, file, ensure_ascii=False, indent=4, cls=Block.BlockJSONEncoder)

    def update(self, *blocks):
        """Updates the blockchain file.
        """

        with open(self.dir + r'\blockchain.json', mode="r+") as file:
            file.seek(0, 2)
            position = file.tell() - 3
            file.seek(position)
            file.write(
                f",\n{json.dumps(dict(enumerate(blocks)), ensure_ascii=False, indent=4, cls=Block.BlockJSONEncoder)[2:-1]}")
            file.write('}')

    # IMPORTANT: load overwrites the blockchain.
    def load(self):
        """
        Loads the blockchain from a json file
        """

        with open(self.dir + r'\blockchain.json', 'r', encoding='utf-8') as file:
            temp_chain = json.load(file)

            self.chain = dict()
            for id, value in temp_chain.items():
                self.chain.update({int(id): Block.decode_JSON(value)})
