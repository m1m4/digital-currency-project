import Block
from Block import Constants
import os
import json
from types import SimpleNamespace


class Blockchain:
    """
    A class that represents the blockchain. It is responsible to manage the blockchain.
    """

    def __init__(self, chain=None):
        """
        The __init__ method of the blockchain. Creates a new blockchain with the first block as GENESIS,
        unless given another chain.

        :param chain: (dictionary) The blockchain in a dictionary. Default is the first GENESIS block.
        """
        if chain is None:
            self.chain = {1: Constants.GENESIS}
        else:
            self.chain = chain

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

    def save(self, dir=None):
        """
        Saves the blockchain to a json file

        :param dir: (str) file directory. Default is the directory of this file
        """

        # Optional custom directory
        if dir is None:
            dir_path = os.path.dirname(os.path.realpath(__file__))
        else:
            dir_path = dir

        with open(dir_path + r'\blockchain.json', 'w', encoding='utf-8') as file:
            json.dump(self.chain, file, ensure_ascii=False, indent=4, cls=Block.BlockJSONEncoder)

    def upadate(self, dir=None, *blocks):
        """
        Updates the blockchain file. if the chain in memory is .

        :param dir: (str) file directory. Default is the directory of this file
        """

        # Optional custom directory
        if dir is None:
            dir_path = os.path.dirname(os.path.realpath(__file__))
        else:
            dir_path = dir

        with open(dir_path + r'\blockchain.json', mode="r+") as file:
            file.seek(0, 2)
            position = file.tell() - 3
            file.seek(position)
            file.write(
                f",\n{json.dumps(dict(enumerate(blocks)), ensure_ascii=False, indent=4, cls=Block.BlockJSONEncoder)[2:-1]}")
            file.write('}')

    # IMPORTANT: load overwrites the blockchain.
    def load(self, dir=None):
        """
        Loads the blockchain from a json file

        :param dir: (optional) file directory. Default is the directory of this file
        """

        # Optional custom directory
        if dir is None:
            dir_path = os.path.dirname(os.path.realpath(__file__))
        else:
            dir_path = dir

        with open(dir_path + r'\blockchain.json', 'r', encoding='utf-8') as file:
            temp_chain = json.load(file)

            self.chain = dict()
            for id, value in temp_chain.items():
                self.chain.update({int(id): Block.decode_JSON(value)})
