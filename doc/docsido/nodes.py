"""Contain all documentation node types.

Each node represent a documentation object and is responsible to output the
correct ReST text in render_rst() method.
"""

def ensure_blank_line_ending(result):
    """If the description didn't end with a blank line add one here."""
    if len(result) > 0 and len(result[-1].strip()) != 0:
        result.append('')


class Node(object):
    """Basic object for a documentation node.
    
    Basic documentation lines container, which does not apply any changes to
    the contained text.
    Can be inherited by complex nodes, that will probably override
    :meth:`render_rst` to output more complex ReST text.
    
    Attributes:
        indent (int): indent index of documentation line
        text (str):  documentation line's text
        parent (docsido.Node): node's parent node. Is `None` for root node.
        children (list): list of child nodes.
        type (str): holds the type of the documented object represented by this
            node. Is `None` if object has no type.
    """
    TAB_LENGTH = 3

    def __init__(self, indent=0, text=None, parent=None):
        self.indent = indent
        self.text = text
        self.parent = parent
        self.children = []
        self.type = None
        
    def attr_str(self): #pylint: disable=no-self-use
        """Return special attributes string for __repr__ use.
        
        Should be overwritten by inherited nodes to print additional data in
        __str__ string.
        """
        return ''

    def __str__(self):
        pattern = '{class_name}({indent}, {text}{others}, children={children})'
        return pattern.format(class_name=self.__class__.__name__,
                              indent=self.indent,
                              text=self.text,
                              others=self.attr_str(),
                              children=self.children)

    def render_rst(self):
        """Return a list of documentation lines for this tree.
        
        Just outputs self.text member as is, and appends children output.
            
        Returns:
            list. List of documentation strings  
        """
        result = []
        if self.text is not None:
            result.append(self.indent_str() + self.text)
        for child in self.children:
            result.extend(child.render_rst())
        # fix list one liner issue
        if self.text is not None and self.text.startswith(('* ', '#. ', '- ')):
            new_result = [' '.join(result)]
            if len(result[-1].strip()) == 0:
                new_result.append('')
            result = new_result
        return result
    
    def indent_str(self):
        """Return spaces string based on node's indentation."""
        return ' ' * (self.indent * self.TAB_LENGTH)

    def type_link(self):
        """Return a ReST string that links to self.type."""
        return ':class:`{type}`'.format(type=self.type)
    
    def replace_by(self, node_type, *args, **kwargs):
        """Replace this node with given node type.
        
        Creates a new node that will fully replace this node's position in the
        syntax tree.
        Can be used to convert simple nodes to more complex node types that
        will output special ReST text.
        
        Args:
            node_type (type): new node type
            args: will be sent to new node constructor
            kwargs: will be sent to new node constructor
            
        Returns:
            docsido.Node. The new replacing node.
        """
        new_node = node_type(self.indent, *args, **kwargs)
        new_node.replace(self)
        return new_node
    
    def replace(self, node):
        """Replace given node in the syntax tree.
        
        Replaces given node by taking over its children, copying its parent,
        and replacing its parent child by self.
        
        Args: 
            node (docsido.Node): the node being replaced
        """
        self.take_over_children(node)
        self.parent = node.parent
        if self.parent is not None:
            self_index = self.parent.children.index(node)
            self.parent.children[self_index] = self
    
    def take_over_children(self, node):
        """Move given node`s children to be self`s children.
        
        It is achieved by copying node`s children list and replacing their
        parents to self.
        
        Args: 
            node (docsido.Node): the node whose children are taken over
        """
        self.children = node.children
        for child in self.children:
            child.parent = self
    
    def remove_empty_children(self):
        """Remove children with empty text."""
        self.children = [child for child in self.children
                         if len(child.text) > 0]


class SimpleTitle(Node):
    """Simple title node.
    
    Representing a simple documentation title line that looks like `title:`, 
    or `title: some text`.
    "title" is replace by the string given in "title" argument in instance
    creation.
    
    Attributes:
        title (str): the title name
        text (str): the additional text in the same line of the title,
            is `None` if there is no such text.
    """

    def __init__(self, indent, title, text):
        super(SimpleTitle, self).__init__(indent, text)
        self.title = title
        
    def attr_str(self):
        """Return title string."""
        return ', title={0}'.format(self.title)

    def render_rst(self):
        """Outputs title as `.. <title>::`.
        
        If has additional text, puts it in a second line.
        Append child node`s text to result.
            
        Returns:
            list. List of documentation strings.
        """
        result = [self.indent_str() + '.. {title}::'.format(title=self.title)]
        
        self.indent += 1
        description = super(SimpleTitle, self).render_rst()
        result.extend(description)
        
        ensure_blank_line_ending(result)
        return result


class Arg(Node):
    """A node for one argument.
    
    Representing an one argument documentation line that looks like
    `arg_name (arg_type): some text` or `arg_name: some text`.
    
    Attributes:
        name (str): argument name
        type (str): argument type, `None` if no type specified
        text (str): argument text
    """

    def __init__(self, indent, arg_name, arg_type, arg_text):
        super(Arg, self).__init__(indent, arg_text)
        self.name = arg_name
        self.type = arg_type
        
    def attr_str(self):
        """Return name and type string."""
        return ', name={0}, type={1}'.format(self.name, self.type)

    def render_rst(self):
        """Outputs argument lines as ReST text.
        
        Outputs `:param <name>: <text>` line, and appends child node`s text.
        If type is specified append in the end `:type <name>: <type link>`.
            
        Returns:
            list. List of documentation strings.
        """
        name = self.name.replace('*', r'\*')
        self.text = ':param {name}: {text}'.format(name=name, text=self.text)
        
        result = super(Arg, self).render_rst()

        # If a type was specified render the type
        if self.type is not None:
            result.append(self.indent_str() + ':type {name}: {type}'.format(
                            name=self.name, type=self.type_link()))
            result.append('')

        ensure_blank_line_ending(result)
        return result


class Output(Node):
    """A node for an output line.
    
    Representing an output documentation line that looks like
    `title: type. some text` or - 
    `title:
        type. some text`.
    
    Attributes:
        title (str): the title name
        type (str): the output type
        text (str): the additional text in the line.
    """
    def __init__(self, indent, title, out_type, text):
        super(Output, self).__init__(indent, text)
        self.title = title
        self.type = out_type

    def render_rst(self):
        """Outputs output lines as ReST text.
        
        Outputs `:<title>: <type> <text>` line, and appends child node`s text.
            
        Returns:
            list. List of documentation strings.
        """
        return_type = ('' if self.type is None
                       else '{0}. '.format(self.type_link()))
        self.text = ':{title}: {type}{text}'.format(
                      title=self.title, type=return_type, text=self.text)
        
        result = super(Output, self).render_rst()
        ensure_blank_line_ending(result)
        return result


class ListItem(Node):
    """An abstract node for a typed item of a listed paragraph.
    
    Inheriting nodes should override :meth:`item_str` method.
    """
    def __init__(self, indent, item_type, text):
        super(ListItem, self).__init__(indent, text)
        self.type = item_type
        
    def attr_str(self):
        return ', type={0}'.format(self.type)
        
    def item_str(self):
        raise NotImplementedError()

    def render_rst(self):
        """Parse text and return a list of child nodes."""
        bullet = '* ' if len(self.parent.children) > 1 else ''
        description = super(ListItem, self).render_rst()
        text = ' '.join(line.strip() for line in description)
        if len(text.strip()) > 0:
            text = ' - ' + text
        
        result = [self.indent_str() + '{bullet}{item}{text}'.format(
                    bullet=bullet, item=self.item_str(), text=text)]

        ensure_blank_line_ending(result)
        return result


class Except(ListItem):
    """A node for one exception line.
    
    Representing one exception documentation line that looks like
    `exception: some text`.
    
    Attributes:
        type (str): the exception type
        text (str): the additional text in the line.
    """
    def item_str(self):
        """Return exception type as ResT link."""
        return self.type_link()


class Attribute(ListItem):
    """A node for an attribute line.
    
    Representing one attribute documentation line that looks like
    `attr_name (attr_type): some text` or `attr_name: some text`.
    
    Attributes:
        name (str): attribute name
        type (str): attribute type, `None` if no type specified
        text (str): attribute text
    """
    def __init__(self, indent, attr_name, attr_type, attr_text):
        super(Attribute, self).__init__(indent, attr_type, attr_text)
        self.name = attr_name
        
    def attr_str(self):
        """Return name and type string."""
        return (', name={0}'.format(self.name) +
                super(Attribute, self).attr_str())
    
    def item_str(self):
        """Return ReST text with name in bold and type as link inside ()."""
        type_text = ('' if self.type is None
                     else ' ({0})'.format(self.type_link()))
        return '**{name}**{type}'.format(name=self.name, type=type_text)
