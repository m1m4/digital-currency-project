import time
from hashlib import *


# Make the first block of the blockchain
def genesis():
    return Block('void', [], 'mima', is_genesis=True)


class Block:

    def __init__(self, last_hash, data, validator, is_genesis=False):

        if is_genesis:
            self.timestamp = 0
        else:
            self.timestamp = time.time()
        self.last_hash = last_hash
        self.data = data
        self.validator = validator

        self.hash = sha256(f'{self.timestamp}{self.last_hash}{self.data}'.encode()).hexdigest()

    def __repr__(self):
        return f'Block({self.timestamp}, {self.hash}, {self.last_hash}, {self.data}, {self.validator})'

    def __str__(self):
        return f'''Time Created: {self.timestamp}
Hash: {self.hash}
Last Hash: {self.last_hash}
Validator name: {self.validator}
Data: {self.data}
        '''
