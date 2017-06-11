"""Parse docstrings by creating a tree of documentation nodes and parsing them.

Parses the given docstring by arranging the text into a tree, based on
headlines and indentation. Each node is parsed according to it's type.
"""
# pylint: disable=unused-argument,protected-access
import re

from itertools import izip, chain

from parser import (ParamNodeParser, OutputNodeParser, ExceptNodeParser,
                    DocsidoError)
from nodes import (Node, SimpleTitle, Arg, Output, Except, Attribute,
                   ensure_blank_line_ending)


class BasicStruct(object):
    """Struct-like object.

    example:
    >>> class MyStruct(BasicStruct):
    ...     __slots__ = ('attr_a', 'attr_b')
    >>> MyStruct(5, attr_b=6)
    MyStruct(attr_a=5, attr_b=6)
    """

    __slots__ = ()  # should be extended by deriving classes

    def __init__(self, *args, **kwargs):
        for key, value in chain(izip(self.__slots__, args),
                                kwargs.iteritems()):
            setattr(self, key, value)

        for key in self.__slots__:
            if not hasattr(self, key):
                setattr(self, key, None)

    def __repr__(self):
        attrs_str = ', '.join('%s=%r' % (key, getattr(self, key))
                              for key in self.__slots__)
        return '%s(%s)' % (self.__class__.__name__, attrs_str)

    def __cmp__(self, other):
        if not isinstance(other, type(self)):
            # if the types are different we want to make sure the comparison
            # result is not 0, but remain consistent, so we compare the types
            return cmp(type(self), type(other))

        return cmp(self._to_tuple(), other._to_tuple())

    def __hash__(self):
        return hash(self._to_tuple())

    def _to_tuple(self):
        return tuple(getattr(self, key) for key in self.__slots__)

    def __getstate__(self):
        return self._to_tuple()

    def __setstate__(self, state):
        for key, value in izip(self.__slots__, state):
            setattr(self, key, value)

    def _to_dict(self):
        return {key: getattr(self, key) for key in self.__slots__}


class IndentLine(BasicStruct):
    """Hold line indentation and text.

    Attributes:
        indent (int): the number of spaces before line starts
        text (str): the text of the line without starting spaces
    """
    __slots__ = ('indent', 'text')


class DocConverter(object):
    """Converts google-style documentation into ReST style documentation.

    The main class of Docsido - responsible to perform all cases of the
    conversion to ReST lines.

    Common usage: `DocConverter(lines, raise_errors, err_handler).convert()`

    Attributes:
        raise_errors (bool): if `True`, errors are raised as DocsidoError,
            if `False`, warning messages are passed to `err_handler`
        err_handler (callable): callable object that receives a string,
            is called for error messages if `raise_errors` is false
        node (docsido.Node): the currently parsed node in the syntax tree
        title (str): the title of currently parsed line
        text (str): the text of currently parsed line

    `node`, `title` and `text` are convert case state attributes.
    """
    TITLE_REGEX = re.compile(r'([a-zA-Z]+):\s*(.*)')

    def __init__(self, raise_errors, err_handler):
        self.raise_errors = raise_errors
        self.err_handler = err_handler
        # convert state
        self.node = None
        self.title = None
        self.text = None

    def convert(self, sphinx_lines):
        """Convert `sphinx_lines` to ReST documentation lines.

        The main method of `DocConverter`.

        Args:
            sphinx_lines (list): a list of Sphinx documentation lines

        Returns:
            list. A list of lines containing the transformed docstring.

        Raises:
            DocsidoError: if `raise_errors` is `True` and found a syntax
                error during parsing.
        """
        indent_lines = self.parse_lines(sphinx_lines)
        syntax_tree = self.make_tree(indent_lines)
        result = syntax_tree.render_rst()
        ensure_blank_line_ending(result)
        return result

    @staticmethod
    def parse_lines(sphinx_lines):
        """Return indent lines with values parsed from `sphinx_lines`.

        For each line in `lines` creates an :class:`IndentLine` instance with
        lines indentation and text.
        Empty lines will have the indentation of above non-empty line.
        Because of the quotation marks in documentation first line, it is
        received by Sphinx with no indentation. To fix this the First line gets
        the indentation of the second line if it`s not empty.

        Args:
            sphinx_lines (list): a list of Sphinx documentation lines

        Returns:
            list. list of :class:`IndentLine` parsed from `sphinx_lines`
        """
        indent_lines = []
        indent = 0
        for line in sphinx_lines:
            text = line.lstrip()
            if len(text) > 0:
                indent = len(line) - len(text)
            indent_lines.append(IndentLine(indent, text))

        # Compute the first line indentation
        if (len(indent_lines) >= 2 and indent_lines[0].indent == 0 and
                len(indent_lines[1].text) > 0):
            indent_lines[0].indent = indent_lines[1].indent
        return indent_lines

    def make_tree(self, indent_lines):
        """Create a syntax_tree based on `indent_lines`.

        Creates the full syntax-tree based on the indentation of the lines and
        the text of each node.

        Args:
            indent_lines (list): list of :class:`IndentLine`

        Returns:
            docsido.Node: the whole documentation syntax tree parsed
                from `indent_lines`
        """
        syntax_tree = self.make_basic_tree(indent_lines)
        self.normalize_indent(syntax_tree)
        self.node = syntax_tree
        self.convert_tree()
        return syntax_tree

    @staticmethod
    def make_basic_tree(indent_lines):
        """Create basic syntax-tree based on `indent_lines`.

        Creates a basic syntax-tree based on the indentation of the lines:
        lines with same indentation are brothers, and a line is a father of
        following lines with bigger indentation.
        Each created node is of the basic :class:`docsido.Node` type.

        Args:
            indent_lines (list): list of :class:`IndentLine`

        Returns:
            docsido.Node: a basic documentation syntax tree parsed
                from `indent_lines`
        """
        syntax_tree = Node()
        current_node = syntax_tree
        for line in indent_lines:
            while (current_node.indent >= line.indent and
                   current_node.parent is not None):
                current_node = current_node.parent
            new_node = Node(line.indent, line.text, current_node)
            current_node.children.append(new_node)
            current_node = new_node
        return syntax_tree

    @classmethod
    def normalize_indent(cls, node):
        """Normalize the indent of given tree.

        In order to make tree parsing easier, takes care that a node's indent
        is 1 above it's parent.
        """
        if node.indent != 0:
            node.indent = node.parent.indent + 1
        for child in node.children:
            cls.normalize_indent(child)

    def convert_tree(self):
        """Convert `self.node` to a specific node type based on its text.

        If node is structures as `title:` or `title: text` and `title` is one
        of supported special titles - converts it to a special node, while
        `self.title` and `self.text` hold the parsed values during the
        conversion process.

        Otherwise - convert each child recursively.

        Raises:
            DocsidoError: if `raise_errors` is `True` and found a syntax
                error during node conversion.
        """
        try:
            self.title, self.text = self.get_node_values()
            if self.title is None:
                for child in self.node.children:
                    self.node = child
                    self.convert_tree()
            else:
                self.TITLE_CONVERTERS[self.title](self)

        except DocsidoError as err:
            if self.raise_errors:
                raise
            self.err_handler(err.message)

    def get_node_values(self):
        """Return node's title and text if is a known type.

        If self.node is a know special title, returns title string and it's
        additional text string, if exists.

        Returns:
            tuple. strings (title, text) of the node, both are None if not a
                known title.
        """
        if self.node.text is None:
            return None, None
        re_res = self.TITLE_REGEX.match(self.node.text)
        if re_res is None:
            return None, None
        title = re_res.group(1).lower()
        text = re_res.group(2)
        text = None if text == '' else text
        if title not in self.TITLE_CONVERTERS.keys():
            return None, None
        return title, text

    def convert_simple_title(self):
        """Convert `self.node` to a :class:`docsido.SimpleTitle` node."""
        self.node.replace_by(SimpleTitle, self.title, self.text)

    def convert_output(self):
        """Convert `self.node` to a :class:`docsido.Output` node.

        First takes care that node`s text contain the first line of the output
        and the children are the additional lines.
        Second converts the title node to :class:`docsido.Output` and
        leaves all children as they are.

        Raises:
            DocsidoError: if there is no, or more than one, output values,
                or if there is a syntax error.
        """
        if self.text is None:
            self.node.remove_empty_children()
            if len(self.node.children) > 1:
                raise DocsidoError('in line "%s": there should be only one '
                                     '"%s" value' % (self.node.children[1].text,
                                                     self.title))
            if len(self.node.children) < 1:
                raise DocsidoError('"%s" title without any value.' %
                                       self.title)
            child = self.node.children[0]
            self.text = child.text
            self.node.take_over_children(child)

        OutputNodeParser(Output, self.title).convert(self.node, self.text)

    def convert_complex_title(self, node_type, item_parser):
        """Convert self.node's children to a given complex node type.

        If `node` contains text, create a new `docsido.Node` with the text
        and insert it as node's first child.

        Node itself is not converted - only its text is modified to contain
        only the title in ReST syntax.
        Node's children are converted to `node_type` using `item_parser`.

        Raises:
            DocsidoError: if there is a syntax error.
        """
        if self.text is not None:
            new_node = Node(self.node.indent + 1, self.text, self.node)
            self.node.children.insert(0, new_node)
        self.node.remove_empty_children()
        for child in self.node.children:
            item_parser(node_type, self.title).convert(child, child.text)
        self.node.text = ':{title}:'.format(title=self.title)

    def convert_args(self):
        """Convert `Args` type tree.

        Convert tree using :meth:`convert_complex_title`
        with node :class:`docsido.Arg`
        and parser class:`docsido.ParamNodeParser`.

        Raises:
            DocsidoError: if there is a syntax error.
        """
        self.convert_complex_title(Arg, ParamNodeParser)
        self.node.text = None
        for child in self.node.children:
            child.indent = self.node.indent

    def convert_raises(self):
        """Convert `Raises` type tree.

        Convert tree using :meth:`convert_complex_title`
        with node :class:`docsido.Except`
        and parser :class:`docsido.ExceptNodeParser`.

        Raises:
            DocsidoError: if there is a syntax error.
        """
        self.convert_complex_title(Except, ExceptNodeParser)

    def convert_attributes(self):
        """Convert `Atrributes` type tree.

        Convert tree using :meth:`convert_complex_title`
        with node class:`docsido.Attribute`
        and parser :class:`docsido.ParamNodeParser`.

        Raises:
            DocsidoError: if there is a syntax error.
        """
        self.convert_complex_title(Attribute, ParamNodeParser)

    TITLE_CONVERTERS = {'note': convert_simple_title,
                        'warning': convert_simple_title,
                        'args': convert_args,
                        'returns': convert_output,
                        'yields': convert_output,
                        'raises': convert_raises,
                        'attributes': convert_attributes}


def default_err_handler(text):
    print 'Warning: %s', text


# unused variables
def rewrite_autodoc(app, obj_type, name, obj, options, lines,
                    err_handler=default_err_handler):
    """Convert lines from google to ReST format.

    The function to be called by the Sphinx autodoc extension when autodoc
    has read and processed a docstring. This function modifies its
    ``lines`` argument *in place* replacing google-style syntax input into
    Sphinx reStructuredText output.

    Args:
        app: The Sphinx application object.

        obj_type: The type of object which the docstring belongs to. One of
            'module', 'class', 'exception', 'function', 'method', 'attribute'

        name: The fully qualified name of the object.

        obj: The object itself.

        options: The options given to the directive. An object with attributes
            ``inherited_members``, ``undoc_members``, ``show_inheritance`` and
            ``noindex`` that are ``True`` if the flag option of the same name
            was given to the auto directive.

        lines: The lines of the docstring.  Will be modified *in place*.

    Raises:
        DocsidoError: if `raise_errors` is `True` and found a syntax error
            during conversion.
    """
    lines[:] = DocConverter(False, err_handler).convert(lines)
