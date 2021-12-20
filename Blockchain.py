import Block
from Block import Constants
import os
import json
from types import SimpleNamespace


class Blockchain:
    """
    A class that represents the blockchain. It is responsible to manage the blockchain.
    """

    def __init__(self, chain=None, dir=None):
        """
        The __init__ method of the blockchain. Creates a new blockchain with the first block as GENESIS,
        unless given another chain.

        :param chain: (dictionary) The blockchain in a dictionary. Default is the first GENESIS block.
        :param dir: (str) the directory of the blockchain. Default is the directory of this file
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

    def add_block(self, data, pow):
        """
        Adds a new Block to the blockchain

        :param data: (list) The trasactions data to add to the blockchain
        :param pow: (str) The proof of work

        :return: The newly added block
        """
        last_block = list(self.chain.values())[-1]

        new_block = Block.Block(last_block.hash, data, pow)
        self.chain.update({len(self.chain) + 1: new_block})

        return new_block

    def print_blocks(self, start=1, end=None):
        """
        Prints the blockchain to console

        :param start: The starting index of the blocks to print. Default is set to 1
        :param end: The ending index of the blocks to print (including itself).
         Default is set to the end of the blockchain
        """
        if end is None:
            end = len(self.chain)

        for id in self.chain:
            if start <= id <= end:
                print(f'Block #{id}:\n' + str(self.chain.get(id)))

    def save(self):
        """
        Saves the blockchain to a json file
        """

        with open(self.dir + r'\blockchain.json', 'w', encoding='utf-8') as file:
            json.dump(self.chain, file, ensure_ascii=False, indent=4, cls=Block.BlockJSONEncoder)

    def update(self, *blocks):
        """
        Updates the blockchain file. if the chain in memory is .
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
