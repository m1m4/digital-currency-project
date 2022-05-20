from os import execv
from wallet import *
from block import *
import blockchain
import random
from collections import namedtuple


def generate_txns(amount, wallet=None):
 
    if not wallet is None:
    
        wallet.debug_generate_outputs(amount * 10, amount)

        txns = []

        for _ in range(amount):
            txns.append(wallet.send(0, ('u1', 5), ('u2', 5)))
            
        return txns
    
    else: 

        txns = []

        for _ in range(amount):
            
            wallet = Wallet()
            wallet.debug_generate_outputs(60, random.randint(1, 5))
            
            addr_len = random.randint(1, 8)
            addrs = []
            for i in range(addr_len):
                addrs.append((generate_invalid_address(), 60 / addr_len))
                
            txns.append(wallet.send(random.randint(1, 10), addrs))
            
        return txns
    

def generate_blocks(blockchain, amount, update=True):
    
    
    last_block = blockchain.last_block(confirmed=False)
    
    if last_block is None:
        last_block = blockchain.last_block()

    else:
        last_block = last_block[0]
        
    for _ in range(amount):
        
        txns = generate_txns(5)
        b = create_block(last_block, txns, random.randint(1, 10))
        blockchain.add_block(b, update_file=update)
        last_block = b
        
    
    
    
    

    

if __name__ == '__main__':
    
    words = 'simple shallow utility impulse humor purse occur image egg joke \
            they boost feel mean relax oval ozone weekend eternal element \
            retreat apart able absent'
            
    # w = Wallet(words)
    
    # bc = blockchain.Blockchain()

    # # generate_blocks(bc, 6, update=False)
    # # # print(type(bc.last_block(confirmed=False)))
    # # print(bc.last_block(confirmed=False)[0])
    # # print(bc.get_block(bc.last_block(confirmed=False)[0]._hash))
    
    # # print(Constants.GENESIS.pack())
    
    
    # bc.load()
    
    # heights = [(5, 1), (5, 3), (5, 2)]
    
    # max_peer = max(heights, key=lambda x:x[1])[0]
    # print(max_peer)
    
    T = namedtuple('A', ['one', 'two'])
    

    t1 = T(1, 2)
    t2 = T(1, 2)
    t3 = (1, 2)
    t4 = T(3, 4)
    
    print(t1 == t2)
    print(t1 == t3)
    print(t1 == t4)
    
    # bc.save()
    
    
    
    

    
    
    
    
            
    



    
    
    

    
    

