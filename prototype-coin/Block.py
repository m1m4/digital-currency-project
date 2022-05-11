import functools
import time
from collections import namedtuple
from hashlib import *
import json

Transaction = namedtuple('Transaction', ['ver', 'sender', 'receivers',
                                         'outputs', 'proof'])
"""Transaction namedtuple. It's a namedtuple named to store all the information
related to the trasaction
Args:
    ver (str): The transaction version. Used to add support to the variety of 
    versions that might come later without making older version invalid.

    sender (str): The sender's address
    
    receivers (tuple): The receivers addresses. correct format for each address
    ([addr],[amount in string]). to add fees change addr to 'FEES'
    
    outputs (tuple): Unspent transaction outputs. Correct format for each output
    is ([block_id], [transaction_id], [output_id]) all in type string

    proof (tuple): A proof that ensures the sender is the owner of this address 
    and its outputs. It consists of a tuple with the public key of the sender
    and the signature of the transaction. 
    
"""

BlockMetadata = namedtuple('BlockMetadata', ['timestamp', 'last_hash',
                                             'proof_of_work', 'block_hash'])
""" Block metadata namedtuple. same as Block but without the Transactions

    Args:
    last_hash (str): the hash of the last block
    
    proof_of_work (str): the proof of work of the block
    
    timestamp (float, optional): the time in unix time the block was 
    created. Defaults to None.
    
    block_hash (str, optional): The hash of this block. Defaults to None.
"""


# The main block class
class Block:

    def __init__(self, last_hash, txns, proof, timestamp=None,
                 _hash=None):
        """The block class. represents a block in the blockchain

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
        self.proof = proof
        self.txns = txns

        if _hash is None:
            self._hash = sha256(f'{self.timestamp}{self.last_hash} \
                        {self.txns}{self.proof}'.encode()).hexdigest()

        self.txns = txns

    def __repr__(self):
        return f'Block({self.timestamp}, {self._hash}, {self.last_hash}, \
{self.proof})'

    def __str__(self):
        return f'Block({self.timestamp}, {self._hash}, {self.last_hash}, \
{self.proof})'

    @functools.cached_property
    def metadata(self):
        return BlockMetadata(self.timestamp, self.last_hash, self.proof,
                             self._hash)

    def json(self):
        return json.dumps(self.__dict__)


def generate_block(block, txns, pow_):

    if block is None:
        return Constants.GENESIS
    else:
        return Block(block._hash, txns, pow_)


def decode_JSON(dict_):
    return Block(dict_["last_hash"], dict_["data"], dict_["pow"],
                 timestamp=dict_["timestamp"], hash=dict_["hash"])


# A Class inheriting from JSONEcoder to encode the Block class to json dict
class ClsEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


# Premade object of the block class
class Constants:
    GENESIS = Block('void', [Transaction('0.1', 'void',
                                         ('mima', 10), None, None)], '0')
