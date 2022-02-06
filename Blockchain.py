import Block
from Block import Constants
import os
import json
import pandas as pd
import pathlib
from TreeNode import TreeNode, strip_short


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

    def add_block(self, block):
        """Adds the given block to the blockchain. If not related to any block
        in the blockchain, it is added to the orphaned blocks list

        Args:
            block (Block): the block to add to the blockchain
        """
        
        def insert(block, root, i=0):
            """Inserts a block to the unconfirmed blockchain. returns false if
            not found a previous block

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
            elif block.last_hash == root.data.hash:
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
            if block.last_hash == self.chain[-1].hash:
                self.unconfirmed = TreeNode(block)
            else:
                self.orphaned_blocks.append(block)
        
       
        if not insert(block, self.unconfirmed):
            self.orphaned_blocks.append(block)
         
         # Remove all short forks   
        strip_short(self.unconfirmed, 2)
        
        # If the block height is more than 3 and there no forks, add to the main
        # chain
        if self.unconfirmed.max_level() >= 3 and \
            len(self.unconfirmed.children) == 1:
            
            self.chain.append(self.unconfirmed.data)
            self.unconfirmed = self.unconfirmed.children[0]
            self.unconfirmed.remove_parent()
            
            
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
            have 1 parameter for the chain in memory. Defaults to None.
        """
        
        if func is None:
            
            metadata_list = list()
            txns_list = list()
            for block in self.chain:
                metadata_list.append([block.timestamp, block.last_hash, 
                                      block.pow, block.hash, len(txns_list) + 1,
                                      len(block.txns)])
                
                txns_list += block.txns
                
            metadata_df = pd.DataFrame(metadata_list,
                                       columns=['Timestamp', 'Last hash', 'POW',
                                                'Hash', 'Line in txns',
                                                'Amount of txns'])
            
            txns_df = pd.DataFrame(txns_list)
            
            metadata_df.to_csv(r'metadata.csv')
            txns_df.to_csv(r'txns.csv')
        
        else:
            func(self.chain)

    # IMPORTANT: load overwrites the blockchain.
    def load(self):
        """Loads the blockchain from a json file
        """

        with open(self.dir + r'\blockchain.json', 'r', encoding='utf-8') as file:
            temp_chain = json.load(file)

            self.chain = dict()
            for id, value in temp_chain.items():
                self.chain.update({int(id): Block.decode_JSON(value)})
                
    def get_last_block(self, confirmed=True):
        
        if confirmed:
            return self.chain[-1]
                
                
