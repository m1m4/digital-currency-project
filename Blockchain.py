import Block


class Blockchain():

    def __init__(self):
        self.chain = [Block.genesis()]

    def add_block(self, data):
        block = Block.Block(self.chain[-1])
