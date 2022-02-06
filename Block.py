import time
import json
from hashlib import *
from json import JSONEncoder
from dataclasses import dataclass, field


#TODO: convert to dataclass
# The main block class
class Block:

    def __init__(self, last_hash, txns, pow, timestamp=None, hash=None):
        """[summary]

        Args:
            last_hash (str): the hash of the last block
            
            txns (tuple): a tuple of all the transaction in the block
            
            pow (str): the proof of work of the block
            
            timestamp (float, optional): the time in unix time the block was 
            created. Defaults to None.
            
            hash (str, optional): The hash of this block. Defaults to None.
        """
        
        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp
        self.last_hash = last_hash
        self.transactions = txns
        self.pow = pow

        if hash is None:
            self.hash = sha256(f'{self.timestamp}{self.last_hash} \
                        {self.transactions}{self.pow}'.encode()).hexdigest()
        else:
            self.hash = hash

    def __repr__(self):
        return f'Block({self.timestamp}, {self.hash}, {self.last_hash}, \
                {self.data}, {self.pow})'

    def __str__(self):
        return json.dumps(self, ensure_ascii=False, indent=4,
                          cls=ClsEncoder)


# A Class inheriting from JSONEcoder to encode the Block class to json dict
class ClsEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def decode_JSON(dict_):
    return Block(dict_["last_hash"], dict_["data"], dict_["pow"],
                 timestamp=dict_["timestamp"], hash=dict_["hash"])


# Premade object of the block class
class Constants:
    GENESIS = Block('void', [], '0')

