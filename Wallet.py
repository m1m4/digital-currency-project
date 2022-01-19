import json
from collections import namedtuple
from Block import ClsEncoder

import binascii
import mnemonic
import bip32utils


Transaction = namedtuple('Transaction', ['ver', 'sender', 'receivers',
                                         'outputs', 'proof'])
"""Transaction namedtuple. It's a namedtuple named to store all the information
related to the trasaction
Args:
    ver (str): The transaction version. Used to add support to the variety of 
    versions that might come later without making older version invalid.

    sender (str): The sender's address
    
    receivers (tuple): The receivers addresses. correct format for each address
    ([addr],[amount]). to add fees change addr to 'FEES'
    
    outputs (tuple): Unspent transaction outputs. Correct format for each output
    is ([block_id], [transaction_id], [output_id])

    proof (tuple): A proof that ensures the sender is the owner of this address 
    and its outputs. It consists of a tuple with the public key of the sender
    and the signature of the transaction. 
    
"""
    


class Wallet:

    def __init__(self, mnemonic_words=None):
        """Class for handling the hd wallet. Currently uses bip39 standard with
        only 1 account and no categories.
        generates an hd wallet with on the coin's network

        Args:
            mnemonic_words (str): mnomic words to make the keys from
        """
        
        mnemo = mnemonic.Mnemonic("english")

        if mnemonic_words is None:
            mnemonic_words = mnemo.generate(strength=256)

        
        seed = mnemo.to_seed(mnemonic_words)

        # DO NOT share this key
        master_key = bip32utils.BIP32Key.fromEntropy(seed) 
        
        # This is the master key in path m/44'/69420'/0'/0
        master_coin_key = master_key.ChildKey(
            44 + bip32utils.BIP32_HARDEN
        ).ChildKey(
            69420 + bip32utils.BIP32_HARDEN
        ).ChildKey(
            0 + bip32utils.BIP32_HARDEN
        ).ChildKey(0).ChildKey(0)
   
        self.words = mnemonic_words
        self.addr = master_coin_key.Address()
        self.pub_k = binascii.hexlify(master_coin_key.PublicKey()).decode()
        # Private key is in wif (Wallet import format)
        self.priv_k = master_coin_key.WalletImportFormat() 
        print(master_coin_key.PrivateKey())
        
        self.utxos = set()
    
    
    def __repr__(self):
        return f'Wallet({self.words}, {self.addr}, {self.pub_k}, {self.priv_k})'
    
    def __str__(self):
        return json.dumps(self, ensure_ascii=False, indent=4, cls=ClsEncoder)
    
    def update_utxo(self, blockchain):
        """Get all the unspent transaction token from the blockchain.
        WARNING: might be very slow when the blockchain gets big. It is 
        recommended to use it only once when you reuse a wallet's 
        private key/mnemonic words

        Args:
            blockchain (Blockchain): The blockchain to retrieve the utxos from
        """
        utxo = blockchain.find_txns(self.addr)
    
    def send(self, fee, *recv_addrs):
        """Creates a new transaction to send other nodes

        Args:
            fee (int): the amount of coins to leave as a fee
            
            *recv_addrs (tuple): tuples containing addresses to send to with 
            the amount specified
            

        Raises:
            NotEnoughFundsError: This means the user tried to send more funds 
            than he has in his wallet
        
        Returns:
            namedtuple(Transaction): The newly created transaction
        """
        
        total = 0
        for addr in recv_addrs:
            total += addr[1]
        
        if total > self.get_balance:
            raise NotEnoughFundsError
        
        ver = '0.1'
        
        #TODO: Create better algorithm for choosing the right utxos
        outputs = []
        utxo_val = 0
        for utxo in self.utxos:
            if utxo_val > total:
                break
            
            utxo_val += utxo[3]
            outputs.append((utxo[:-1]))
            
            
        proof = (self.pub_k,)
            
        txn = Transaction(ver, self.addr, recv_addrs + ('FEES', fee), outputs)
        
        
        
        
    def get_balance(self):
        """Sums all the Unspent transaction token to check the wallet's balance

        Returns:
            int: The account balance
        """
        
        bal = 0
        for txn in self.utxos:
            bal += txn[2]
        return bal
    


class NotEnoughFundsError(Exception):
    
    def __init__(self, message="Target wallet doesnt have enough funds"):
        super().__init__(message)
        
    