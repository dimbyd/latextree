# node.py
r'''
Here we define the basic Node class for LatexTree objects
    - defines parent/arguments/children attributes
    - defines basic recursive functions for tree traversal
        - These will be used by `latextree.LatexTree` objects for document processing
        - e.g. tree.write_xml(), tree.write_unicode(), tree.xref_table(), etc
'''

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

from lxml import etree

class Node():
    '''
    Abstract class for LatexTree nodes: has only parent and children
    Additional attributes in derived classes:
        Command: args
        Environment: args
        Content: content (chars)

    Should Node be a sublcass of list?
    - n1.add_child(n2) would become self.append(n2) with some type checking
    - a bit weird ...
    '''
    
    counter = 0 # for debugging

    def __init__(self):
        self.serial_no = Node.counter
        Node.counter += 1
        self.parent = None
        self.children = []

        # taxonomy info (the last one fails for direct subclasses of Node)
        self.species = type(self).__name__                            # itemize
        self.genus   = type(self).__bases__[0].__name__               # List
        self.family  = type(self).__bases__[0].__bases__[0].__name__  # Environment

        # info
        log.info('Node {} created ({})'.format(self.serial_no, self.species))


    def __repr__(self):
        return '{}()'.format(self.species)


    def chars(self, **kwargs):
        s = []
        for child in self.children:
            s.append(child.chars(**kwargs))
        return ''.join(s)


    def pretty_print(self, depth=0):
        s = []
        indent_str = '----'
        s.append(indent_str*depth + repr(self))
        for child in self.children:
            s.append(child.pretty_print(depth=depth+1))
        return '\n'.join(s)


    def xml(self):
        elt_name = self.species
        if elt_name[-1] == '*':
             elt_name = elt_name[:-1] + 'star'
        elt = etree.Element(elt_name)
        for child in self.children:
            elt.append(child.xml())
        return elt
    

    def xml_print(self, enc='utf-8'):
        if enc == 'bytes':
            return etree.tostring(self.xml(), pretty_print=True)
        return etree.tostring(self.xml(), pretty_print=True).decode("utf-8")        


    def append_child(self, node):
        '''
        Add a single child node.
        Use this function instead of node.children.append() so that the
        `parent` attribute is set correctly (needed for tree traversal).
        '''
        # type check (should probably be done in NodeList class)
        if not isinstance(node, Node):
            raise TypeError('Cannot add type {} to LatexTreeNode.children'.format(node.__class__.__name__) )
        
        # set parent and append to children
        node.parent = self
        self.children.append(node)


    def append_children(self, node_list):
        '''
        Add a list of child nodes (batch command for append_child)
        '''
        for node in node_list:
            self.append_child(node)


    def get_ancestor(self, species):
        '''
        Get closest ancestor of a given species.
        Used to access chapter and section numbers in templates
        '''        
        node = self
        while node.parent and not node.species == species:
            node = node.parent
        if node.species == species:
            return node
        return None

    # --------------------
    def get_mpath(self):
        '''
        Not used.
        
        Unique ID. Compute materialized path of the node in the tree.
        Based on index of node among its siblings (i.e. in its parent's list of children)
        This index is converted to its two-digit hex equivalent (max. 256 children)
        The mpath is created by recursive calls to parent nodes until the root is reached.
        Thus we return a dot-separated path of two-digit hex numbers.
        
        These can be used for direct addressing.
        In django views we have used `starts_with` to select subtrees from the database.
        
        How about for hyperlinks to individual elements?
            - but we already have an xref table (which maps labels to node objects)
        A map of label -> mpaths would be useful if it helps us to retreive a
        node (and it's subtree) quickly from a database, but when the tree is live in
        memory the xref table has direct links to the objects.
        
        This direct addressing might be handy for hyperlinks between documents, e.g we 
        might append the mpath to a document identifier
        '''
        if not self.parent:
            return ''
        idx = self.parent.children.index(self)
        hexstr = hex(idx)[2:].zfill(2)
        return self.parent.get_mpath() + '.' + hexstr


class NodeList(list):
    '''
    List of Node objects. Implements basic type checking. 
    Simple extension of `list` is useful for debugging.
    '''
    counter = 0
    def __init__(self):
        self.number = NodeList.counter
        NodeList.counter += 1
        list.__init__(self) 
        log.info('NodeList {} created'.format(self.number))

    def append(self, node):
        if not isinstance(node, Node):
            Exception('NodeList objects can only contain Node objects')
        super(NodeList, self).append(node)
        log.debug('{} appended to Nodelist {}'.format(node, self.number))


def test_node():
    pass

if __name__ == '__main__':
    test_node()
