import time
from hashlib import *
from json import JSONEncoder
import json


# The main block class
class Block:

    def __init__(self, last_hash, transactions, pow, timestamp=None, hash=None):

        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp
        self.last_hash = last_hash
        self.transactions = transactions
        self.pow = pow

        if hash is None:
            self.hash = sha256(f'{self.timestamp}{self.last_hash}{self.transactions}{self.pow}'.encode()).hexdigest()
        else:
            self.hash = hash

    def __repr__(self):
        return f'Block({self.timestamp}, {self.hash}, {self.last_hash}, {self.data}, {self.pow})'

    def __str__(self):
        return json.dumps(self, ensure_ascii=False, indent=4, cls=BlockJSONEncoder)

    def verify(self, last_block, difficulty):
        return self.last_hash == last_block.hash and self.hash.startswith(''.zfill(difficulty))
        # TODO: change the difficulty variable so that is matches the mining process


class Transaction:
    """
    The Transaction class. an object that holds important details on each transaction
    """
    def __init__(self, sender, receiver, amount, utxo, signature):
        """
        The constructor.
        :param sender: (string) The sender's public key
        :param receiver: (string) The reciever's public key
        :param amount: (float) The amount to send
        :param utxo: (list(tuple(block, i))) A list of trasaction IDs with unspent transaction outputs of the sender
        :param signature:
        :return:
        """
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.utxo = utxo
        self.signature = signature

    def to_list(self):
        return [self.sender, self.receiver, self.amount, self.utxo, self.signature]


# A Class inheriting from JSONEcoder to encode the Block class to json dict
class BlockJSONEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def decode_JSON(dict_):
    return Block(dict_["last_hash"], dict_["data"], dict_["pow"], timestamp=dict_["timestamp"], hash=dict_["hash"])


# Premade object of the block class
class Constants:
    GENESIS = Block('void', [], '0')

