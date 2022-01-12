import time
from hashlib import *
from json import JSONEncoder
import json
from dataclasses import dataclass, field
import binascii
import mnemonic
import bip32utils


#TODO: convert to dataclass
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
        return json.dumps(self, ensure_ascii=False, indent=4, cls=ClassJSONEncoder)

    def verify(self, last_block, difficulty):
        return self.last_hash == last_block.hash and self.hash.startswith(''.zfill(difficulty))
        # TODO: change the difficulty variable so that is matches the mining process


@dataclass
class Transaction:
    """[summary]
    
    Args:
        sender (str): The sender's public key
        receiver (str): The receiver's address
        amount (int): The amount of coins
        signature (str): The signature of the transaction
        utxo (tuple): Unspent transaction outputs. Correct format for each output is ([block_id],[transaction_id])
    """

    sender: str
    receiver: str
    amount: int
    signature: str
    utxo: tuple = field(default_factory=tuple)

    def calc(self):
        print('calc')


class Wallet:

    def __init__(self, mnemonic_words=None):
        """[summary]
        
        Class for handling the hd wallet. Currently uses bip39 standard with only 1 account and no categories.
        generates an hd wallet with on the coin's network

        Args:
            mnemonic_words (str): mnomic words to make the keys from
        """
        
        mnemo = mnemonic.Mnemonic("english")

        if mnemonic_words is None:
            mnemonic_words = mnemo.generate(strength=256)

        
        seed = mnemo.to_seed(mnemonic_words)

        master_key = bip32utils.BIP32Key.fromEntropy(seed) # DO NOT share this key
        master_coin_key = master_key.ChildKey(
            44 + bip32utils.BIP32_HARDEN
        ).ChildKey(
            69420 + bip32utils.BIP32_HARDEN
        ).ChildKey(
            0 + bip32utils.BIP32_HARDEN
        ).ChildKey(0).ChildKey(0)
   
        self.words = mnemonic_words
        self.addr = master_coin_key.Address(),  
        self.pub_k = binascii.hexlify(master_coin_key.PublicKey()).decode()
        self.priv_k = master_coin_key.WalletImportFormat() # Private key is in wif
        
        
    def __repr__(self):
        return f'Wallet({self.words}, {self.addr}, {self.pub_k}, {self.priv_k})'
    
    def __str__(self):
        return json.dumps(self, ensure_ascii=False, indent=4, cls=ClassJSONEncoder)
    


# A Class inheriting from JSONEcoder to encode the Block class to json dict
class ClassJSONEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def decode_JSON(dict_):
    return Block(dict_["last_hash"], dict_["data"], dict_["pow"], timestamp=dict_["timestamp"], hash=dict_["hash"])


# Premade object of the block class
class Constants:
    GENESIS = Block('void', [], '0')

