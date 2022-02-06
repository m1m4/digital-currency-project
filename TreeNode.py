
class TreeNode:
    def __init__(self, data, parent=None):
        """A class that represent a general tree

        Args:
            data (any): The data of this node
            parent (TreeNode) t
        """
        self.data = data
        self.children = []
        
        
        if not parent is None:
            parent.add_child(self)
        else:
            self.parent = parent

    def get_level(self):
        """Gets the level of the current node

        Returns:
            int: The level
        """
        level = 0
        p = self.parent
        while p:
            level += 1
            p = p.parent

        return level

    def print_tree(self):
        """Prints the tree to the console
        """
        spaces = ' ' * self.get_level() * 3
        prefix = spaces + "|__" if self.parent else ""
        print(prefix + self.data)
        if self.children:
            for child in self.children:
                child.print_tree()

    def add_child(self, child):
        """Adds a child to this node

        Args:
            child (TreeNode): The child node
        """
        child.parent = self
        self.children.append(child)  
    
    def remove_child(self, child):
        """Removes a child

        Args:
            child (TreeNode): The child
        """
        child.parent = None
        self.children.remove(child)
        
    def remove_parent(self):
        """Removes this Node's parent
        """
        self.parent.remove_child(self)
        
    def max_level(self, level=0, i=0):
        """Gets the longest level of a TreeNode

        Args:
            level (int, optional): Used for recursion. do not use.
            i (int, optional): Used for recursion. do not use.

        Returns:
            int: The longest level
        """
    
        if i < len(self.children) - 1:
            return max(self.children[i].max_level(level + 1),
                        self.max_level(level, i + 1))
        
        elif i == len(self.children) - 1:
            return self.children[i].max_level(level + 1)
        
        else:
            return level

        
    def min_level(self, level=0, i=0):
        """Gets the shortest level of a TreeNode

        Args:
            level (int, optional): Used for recursion. do not use.
            i (int, optional): Used for recursion. do not use.

        Returns:
            int: The shortest level
        """
    
        if i < len(self.children) - 1:
            return min(self.children[i].min_level(level + 1),
                        self.min_level(level, i + 1))
        
        elif i == len(self.children) - 1:
            return self.children[i].min_level(level + 1)
        
        else:
            return level
        

def strip_short(root, diff):
    """Removes all short paths that are short than the longest path - diff

    Args:
        root (TreeNode): The root of the Tree
        diff (int): The difference between the longest path and allowed path

    Returns:
        [type]: [description]
    """
    max_level = root.max_level() - 1
    
    for child in root.children:
        if max_level - child.max_level() > diff:
            child.remove_parent()
            
    return root
            
            
def find(value, root, i=0):
    
    # Return false if there's no children
    if root == None:
        return False
    
        # Return True if found
    elif value == root.value:
        return True, root
    
    else:
        return find(value, root.children[i], i) or \
            find(value, root.children[i + 1], i + 1)
            
def insert(value, root, node=TreeNode(None), i=0):
    
    # Return false if there's no children
    if root == None:
        return False
    
        # Return True if found
    elif value == root.value:
        root.add_child(node)
        return True
    
    else:
        return find(value, root.children[i], i) or \
            find(value, root.children[i + 1], i + 1)
    
           
if __name__ == '__main__':
    
    root = TreeNode('noam')
    n1 = TreeNode('n1')
    n2 = TreeNode('n2')
    n21 = TreeNode('n21')
    n211 = TreeNode('n211')
    n2111 = TreeNode('n2111')
    n3 = TreeNode('n3')
    
    root.add_child(n1)
    root.add_child(n2)
    root.add_child(n3)
    
    n2.add_child(n21)
    n21.add_child(n211)
    n211.add_child(n2111)
    
    root.print_tree()
    strip_short(root, 2).print_tree()
    
    print(root)
        