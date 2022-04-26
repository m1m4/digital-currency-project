from wallet import *
from block import *
import blockchain
import random


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
        
        txns = generate_txns(50)
        b = generate_block(last_block, txns, random.randint(1, 10))
        bc.add_block(b, update_file=update)
        last_block = b
        
    
    

    

if __name__ == '__main__':
    
    words = 'simple shallow utility impulse humor purse occur image egg joke \
            they boost feel mean relax oval ozone weekend eternal element \
            retreat apart able absent'
            
    w = Wallet(words)
    
    bc = blockchain.Blockchain()

    generate_blocks(bc, 6, update=False)
    # print(type(bc.last_block(confirmed=False)))
    print(bc.last_block(confirmed=False)[0])
    print(bc.get_block(bc.last_block(confirmed=False)[0]._hash))
    
    
    # bc.load()

    # bc.save()
    
    
    
    

    
    
    
    
            
    



    
    
    

    
    

