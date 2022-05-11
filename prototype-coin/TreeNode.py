
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
        print(prefix + str(self.data))
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


def find(data, root, i=0):
    """finds a Treenode with the given data

    Args:
        data (_type_): The data to find
        root (_type_): The root
        i (int, internal): Used for recursiveness.

    Returns:
        _type_: _description_
    """

    # Return false if there's no children
    if root is None:
        return False, None

        # Return True if found
    elif data == root.data:
        return True, root

    elif i == len(root.children):
        return False, None

    else:
        return find(data, root.children[i], 0) or \
            find(data, root, i + 1)


def findattr(data, attr, root, i=0):
    """finds a Treenode with the given data

    Args:
        data (_type_): The data to find
        root (_type_): The root
        i (int, internal): Used for recursiveness.

    Returns:
        _type_: _description_
    """

    # Return false if there's no children
    if root is None:
        return False, None

        # Return True if found
    elif data == getattr(root.data, attr):
        return True, root

    elif i == len(root.children):
        return False, None

    else:
        return findattr(data, attr, root.children[i], 0) or \
            findattr(data, attr, root, i + 1)


def insert(data, root, new_data=None, i=0):
    """If the data is matched, insert node as a child

    Args:
        data (any): The data
        root (TreeNode): The tree's root
        new_data (any, optional): The new data to insert. Defaults to None.
        i (int, optional): used for recursion. Dot not use. Defaults to 0.

    Returns:
        bool: return True if found, else false
    """
    # Return false if there's no children
    if root == None:
        return False

        # Return True if found
    elif data == root.data:
        root.add_child(TreeNode(new_data))
        return True

    elif i == len(root.children):
        return False

    else:
        return insert(data, root.children[i], new_data, 0) or \
            insert(data, root, new_data, i + 1)


def get_end_children(node, i=0):
    if not node.children:
        return [node]

    elif len(node.children) == 1:
        return get_end_children(node.children[0])

    elif i == len(root.children):
        return []

    else:
        return get_end_children(node.children[i], 0) + \
            get_end_children(node, i + 1)


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
