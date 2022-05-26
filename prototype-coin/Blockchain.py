import os
from typing import List, Optional

import pandas as pd

import treenode
from block import Block, Constants, Transaction
from treenode import TreeNode, get_end_children, strip_short


class Blockchain:

    def __init__(self, chain: Optional[List[Block]]=None,
                 data_dir: Optional[str]=None):
        """A class that represents the blockchain. It is responsible to manage
        the blockchain.

        Args:
            chain (Optional[List[Block]], optional): The confirmed blockchain 
            (If exists). Defaults to None.
            
            data_dir (Optional[str], optional): The default directory to save the blockchain 
            in.
            
        Attributes:
            chain (list): The blocks with height >= 3 and most likely of the
            main chain

            unconfirmed (TreeNode): blocks with height < 3. May include 
            temporary forks in the form of list inside lists


            orphan_blocks: Block that were added to the blockchain but currently
            not related to any block in the blockchain
        """
    

        if chain is None:
            self.chain = [Constants.GENESIS]
        else:
            self.chain = chain
            
        if data_dir is None:
            self.data_dir = 'blockchain'
        else:
            self.data_dir = data_dir
        
        self.PATH = os.path.join(os.path.dirname(__file__), self.data_dir)
        print(f'BLOCKCHAIN - blockchain directory is set to: {self.PATH}')
        
        # Create directories if they not exist
        os.makedirs(os.path.dirname(self.PATH + '//metadata.csv'),
                    exist_ok=True)
        os.makedirs(os.path.dirname(self.PATH + '//txns.csv'),
                    exist_ok=True)

        # TODO: change default value to an empty treenode
        self.unconfirmed = None
        self.orphaned_blocks = list()
        


    def add_block(self, block: Block,
                  is_confirmed: bool=False,
                  other_chain: Optional[List[Block]]=None, 
                  update_file: bool=True):
        """Adds the given block to the blockchain. If not related to any block
        in the blockchain, it is added to the orphaned blocks list

        Args:
            block (Block): The block to add to the blockchain.
            
            is_confirmed (bool, optional): Tells the function if the block is 
            valid. Use with caution since enabling it will insert it into the 
            blockchain even if hashes doesn't match. Defaults to False.
            
            other_chain (Optional[List[Block]]): When set, Writes the block to 
            another chain when is_confirmed = True, it is recommended to also 
            set update_file to false since it will write blocks that dont exist 
            in the main chain. Defaults To None
            
            update_file (bool, optional): Update the blockchain in the disk when
            this block is placed. Defaults to True.
        """
        
        chain = self.chain if other_chain is None else other_chain

        # If it's already was checked
        if is_confirmed:
            
            if chain[-1]._hash == block.last_hash:
                chain.append(block)
                print('BLOCKCHAIN - Added block to confirmed chain')
                
                if update_file:
                    self._update_file(self.last_block())
                    
                return True
            else:
                print('BLOCKCHAIN - Tried to add block to confirmed chain without matching hash')
                return False

        def __insert(block, root, i=0):
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
                return __insert(block, root.children[i], 0) or \
                    __insert(block, root, i + 1)

        # Check if unconfirmed block is empty and check if last block is on
        # confirmed chain
        if self.unconfirmed is None:
            if block.last_hash == self.chain[-1]._hash:
                self.unconfirmed = TreeNode(block)
                print('BLOCKCHAIN - First block is added to unconfirmed chain')
                return True
            else:
                self.orphaned_blocks.append(block)
                print('BLOCKCHAIN - Block is added to orphaned blocks')
                return False

        result = __insert(block, self.unconfirmed)
        if not result:
            self.orphaned_blocks.append(block)
            print('BLOCKCHAIN - Block is added to orphaned blocks')
            return False
        
        else:
            print('BLOCKCHAIN - Block is added to unconfirmed chain')
            

        # Remove all short forks
        strip_short(self.unconfirmed, 2)

        # If the block height is more than 3 and there are no forks, add  it to
        # the main chain
        if self.unconfirmed.max_level() >= 3 and \
                len(self.unconfirmed.children) == 1:

            self.chain.append(self.unconfirmed.data)
            self.unconfirmed = self.unconfirmed.children[0]
            self.unconfirmed.remove_parent()
            print('BLOCKCHAIN - Block is moved to confirmed chain')

            if update_file:
                self._update_file(self.last_block())
        
        return True

    
    def add_blocks(self, blocks: List[Block],
                   is_confirmed: bool=False,
                   update_file: bool=True):
        """Adds multiple blocks to the blockchain, more precisely calls 
        add_block(is_confirmed, update_file) for each block in list

        Args:
            blocks (List[Block]): The blocks to add
            
            is_confirmed (bool, optional): Tells the function if the block is 
            valid. Use with caution since enabling it will insert it into the 
            blockchain even if hashes doesn't match. Defaults to False.
            
            update_file (bool, optional): Update the blockchain in the disk when
            this block is placed. Defaults to True.
        """
        
        for block in blocks:
            self.add_block(block, is_confirmed=is_confirmed, update_file=update_file)

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

    # TODO: imporve save function
    def save(self, func=None):
        """Save the blockchain in memory to the disk using the default method or
        a custom one

        Args:
            func (function, optional): The custom function. function needs to
            have 1 parameter for this blockchain instance. Defaults to None.
        """
        
        print('BLOCKCHAIN - Saving to disk')

        if not func is None:
            return func(self)
        
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

        metadata_df.to_csv(f'{self.PATH}//metadata.csv', index=False)
        txns_df.to_csv(f'{self.PATH}//txns.csv', index=False)


    def load(self, func=None):
        """Loads the blockchain from metadata and txns. WARNING: overwrites
        self.chain and clears the unconfirmed blocks

        Args:
            func (function, optional): The custom function. function needs to
            have 1 parameter for this blockchain instance. Defaults to None.
        """
        print('BLOCKCHAIN - Loading from disk')
        
        if func is None:

            success = False
            metadata_df = pd.read_csv(f'{self.PATH}//metadata.csv')
            total_txns_df = pd.read_csv(f'{self.PATH}//txns.csv')

            temp_chain = [Constants.GENESIS]

            for i, row in metadata_df.iterrows():

                timestamp = row['Timestamp']
                last_hash = row['Last hash']
                proof = row['POW']
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

                block = Block(last_hash, txns, proof, timestamp, _hash)
                self.add_block(block, is_confirmed=True, other_chain=temp_chain,
                               update_file=False)

            # Keep unconfirmed blocks if the hashes match
            if not self.unconfirmed is None and \
                    self.last_block(confirmed=True)._hash == self.unconfirmed.data.last_hash:
                self.unconfirmed = None
                
            return True if len(temp_chain) > 1 else False

        else:
            func(self)

    def _update_file(self, block):

        print('BLOCKCHAIN - Updating blockchain on disk')
        
        txns_df = pd.read_csv(f'{self.PATH}//txns.csv')
        
        block_metadata_df = pd.DataFrame([block.metadata + 
                                          (txns_df.shape[0] +
                                           1, len(block.txns))])
        
        block_txns_df = pd.DataFrame(block.txns)

        block_metadata_df.to_csv(f'{self.PATH}//metadata.csv',
                                 mode='a',
                                 header=not os.path.exists(f'{self.PATH}//metadata.csv'),
                                 index=False)
        block_txns_df.to_csv(f'{self.PATH}//txns.csv',
                             mode='a',
                             header=not os.path.exists(f'{self.PATH}//txns.csv'),
                             index=False)

    def last_block(self, confirmed: bool=True):
        """Return the last block of the blockchain. if confirmed is set to false
        multiple blocks might be returned 

        Args:
            confirmed (bool, optional): If set to true it will get the
            last confirmed block. Defaults to True.

        Returns:
            Union[Block, List[Block]]: The last block/s
        """
        if confirmed:
            return self.chain[-1]
        elif self.unconfirmed is None:
            return None
        else:
            return [block.data for block in get_end_children(self.unconfirmed)]

    # TODO: add cache? + faster function for checking existance
    def get_block(self, _hash: str) -> Block:
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

    def height(self, unconfirmed: bool=False) -> int:
        """Returns the height of this blockchain

        Args:
            unconfirmed (bool, optional): If set to true it gets the height
            including the longest unconfirmed part. Defaults to False.

        Returns:
            int: The height
        """
        if unconfirmed:
            try:
                return len(self.chain) + self.unconfirmed.max_level() + 1
            except AttributeError:
                return len(self.chain)
        else:
            return len(self.chain)
