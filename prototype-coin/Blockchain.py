import os

import pandas as pd

from block import Block, Constants, Transaction
from treenode import TreeNode, get_end_children, strip_short
import treenode


class Blockchain:

    def __init__(self, chain=None):
        """A class that represents the blockchain. It is responsible to manage
        the blockchain.
        
        Args:
            chain (dict, optional): The blockchain. Defaults to Only genesis
            block.
        
        Attributes:
            chain (list): The blocks with height >= 3 and most likely of the
            main chain
            
            unconfirmed (TreeNode): blocks with height < 3. May include temporary
            forks in the form of list inside lists
            
            
            orphan_blocks: Block that were added to the blockchain but currently
            not related to any block in the blockchain
        """
        if chain is None:
            self.chain = [Constants.GENESIS]
        else:
            self.chain = chain
            
        self.unconfirmed = None
        self.orphaned_blocks = list()

    def add_block(self, block, is_confirmed=False, update_file=True):
        """Adds the given block to the blockchain. If not related to any block
        in the blockchain, it is added to the orphaned blocks list

        Args:
            block (Block): the block to add to the blockchain
        """
        
        # If it's already was checked
        if is_confirmed:
            self.chain.append(block)
            
            if update_file:
                self.__update_file(self.last_block())
            
        else:
            def insert(block, root, i=0):
                """Inserts a block to the unconfirmed blockchain. returns false
                if not found a previous block

                Args:
                    block (Block): The block to insert
                    root (TreeNode): The blockchain to insert to
                    i (int, optional): Used for recursion purposes

                Returns:
                    bool: return true if found previous block
                """
                # Return false if there's no children
                if root == None:
                    return False
                
                    # Return True if found
                elif block.last_hash == root.data._hash:
                    root.add_child(TreeNode(block))
                    return True
                
                elif i == len(root.children):
                    return False
                
                else:
                    return insert(block, root.children[i], 0) or \
                        insert(block, root, i + 1)
                
            # Check if unconfirmed block is empty and check if last block is on
            # confirmed chain
            if self.unconfirmed is None:
                if block.last_hash == self.chain[-1]._hash:
                    self.unconfirmed = TreeNode(block)
                else:
                    self.orphaned_blocks.append(block)
            
        
            if not insert(block, self.unconfirmed):
                self.orphaned_blocks.append(block)
            
            # Remove all short forks   
            strip_short(self.unconfirmed, 2)
            
            # If the block height is more than 3 and there no forks, add to the 
            # main chain
            if self.unconfirmed.max_level() >= 3 and \
                len(self.unconfirmed.children) == 1:
                
                self.chain.append(self.unconfirmed.data)
                self.unconfirmed = self.unconfirmed.children[0]
                self.unconfirmed.remove_parent()
                
                if update_file:
                    self.__update_file(self.last_block())
                
            


    
    def print_blocks(self, start=1, end=None):
        """Prints the blockchain to console. Use only when blockchain is very
        small

        Args:
            start (int, optional): start block index. Defaults to 1.
            
            end ([type], optional): end block index. Defaults to the last block.
        """
        if end is None:
            end = len(self.chain)

        for id in self.chain:
            if start <= id <= end:
                print(f'Block #{id}:\n' + str(self.chain.get(id)))

    def save(self, func=None):
        """Save the blockchain in memory to the disk using the default method or
        a custom one

        Args:
            func (function, optional): The custom function. function needs to
            have 1 parameter for this blockchain instance. Defaults to None.
        """
        
        if func is None:
            
            metadata_list = list()
            txns_list = list()
            for block in self.chain:
                metadata_list.append([block.timestamp,
                                      block.last_hash, 
                                      block.proof, block._hash,
                                      len(txns_list),
                                      len(block.txns)])
                
                txns_list += block.txns
                
            metadata_df = pd.DataFrame(metadata_list,
                                       columns=['Timestamp', 'Last hash', 'POW',
                                                'Hash', 'Line', 'Length'])
            
            txns_df = pd.DataFrame(txns_list)
            
            metadata_df.to_csv(r'Blockchain\metadata.csv')
            txns_df.to_csv(r'Blockchain\txns.csv')
        
        else:
            func(self)
   
    # IMPORTANT: load overwrites the blockchain.
    def load(self, func=None):
        """Loads the blockchain from metadata and txns. WARNING: overwrites the
        current
        
        Args:
            func (function, optional): The custom function. function needs to
            have 1 parameter for this blockchain instance. Defaults to None.
        """
        
        if func is None:
            metadata_df = pd.read_csv(r'Blockchain\metadata.csv')
            total_txns_df = pd.read_csv(r'Blockchain\txns.csv')
            
            self.chain = []
            
            for i, row in metadata_df.iterrows():
            
                timestamp = row['Timestamp'] 
                last_hash = row['Last hash']
                pow_ = row['POW'] 
                _hash = row['Hash']
                
                line = row['Line']
                length = row['Length']
                txns_df = total_txns_df.iloc[line:line + length + 1]
                
                txns = []
                for g, txn_row in txns_df.iterrows():
                    txns.append(Transaction(txn_row['ver'], txn_row['sender'],
                                            txn_row['receivers'],
                                            txn_row['outputs'], 
                                            txn_row['proof']))
                
                block = Block(last_hash, txns, pow_, timestamp, _hash)
                self.add_block(block, is_confirmed=True)
            
            if not self.unconfirmed is None and \
            self.last_block(confirmed=True).hash == self.unconfirmed.data.last_hash:
                self.unconfirmed = None
                
        else:
            func(self)
        
    def __update_file(self, block):
        
        block_metadata_df = pd.DataFrame([block.metadata])
        block_txns_df = pd.DataFrame(block.txns)
        
        block_metadata_df.to_csv(r'Blockchain\metadata.csv', mode='a',
                                    header=not os.path.exists(r'Blockchain\metadata.csv'))
        block_txns_df.to_csv(r'Blockchain\txns.csv',  mode='a',
                                    header=not os.path.exists(r'Blockchain\txns.csv'))
        
       
    def last_block(self, confirmed=True):
        
        if confirmed:
            return self.chain[-1]
        elif self.unconfirmed is None:
            return None
        else:
            return [block.data for block in get_end_children(self.unconfirmed)]
        
    def get_block(self, _hash):
        """Retrieves a block from the blockchain by a given hash

        Args:
            _hash (str): The hash

        Returns:
            Block: The block that was found. returns None if not found
        """
        
        for block in self.chain:
            if block._hash == _hash:
                return block
        
        found, block = treenode.findattr(_hash, '_hash', self.unconfirmed, )
        
        if block is None:
            return
        else:
            return block.data
                
            
        

                
                
