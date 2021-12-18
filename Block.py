import time
from hashlib import *
from json import JSONEncoder


def decode_JSON(dict_):
    return Block(dict_["last_hash"], dict_["data"], dict_["pow"], timestamp=dict_["timestamp"], hash=dict_["hash"])


# The main block class
class Block:

    def __init__(self, last_hash, data, pow, timestamp=None, hash=None):

        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp
        self.last_hash = last_hash
        self.data = data
        self.pow = pow

        if hash is None:
            self.hash = sha256(f'{self.timestamp}{self.last_hash}{self.data}{self.pow}'.encode()).hexdigest()
        else:
            self.hash = hash

    def __repr__(self):
        return f'Block({self.timestamp}, {self.hash}, {self.last_hash}, {self.data}, {self.pow})'

    def __str__(self):
        return f'''Time Created: {self.timestamp}
Hash: {self.hash}
Last Hash: {self.last_hash}
Data: {self.data}
Proof of work: {self.pow}
        '''


# A Class inheriting from JSONEcoder to encode the Block class to json dict
class BlockJSONEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


# Premade object of the block class
class Constants:
    GENESIS = Block('void', [], '0')

