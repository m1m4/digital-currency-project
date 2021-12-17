import Block
import os


def save_chain(blockchain):
    pass


def load_chain(dir=None):

    if dir is None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
    else:
        dir_path = dir




class Blockchain():

    def __init__(self, chain=None):

        if chain is None:
            self.chain = [Block.genesis()]
        else:
            self.chain = chain

        self.chain_len = len(chain)

    def add_block(self, data, pow):
        # Adds a new Block to the blockchain
        last_block = Block.Block(self.chain[-1])

        new_block = Block(self.chain_len, last_block.hash, data, pow)
        self.chain.append(new_block)
        self.chain_len += 1
        self.save_blockchain()





