"""Collection of documentation parsers."""

import re
import abc

from sphinx.errors import ExtensionError


TYPE_REGEX = r'~?[\w\.]+'


class DocsidoError(ExtensionError):
    """An exception type specific to the Docsido Sphinx extension."""
    pass


class BasicNodeParser(object):
    """An abstract parser that converts a node based on parsing a text.
    
    Common usage: `InheritingParser(new_node_type, title).convert(node, text)`
    
    Attributes:
        new_node_type (type): the type of the new node.
        title (str): title name.    
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def regex(self):
        raise NotImplementedError()
    
    def __init__(self, new_node_type, title):
        self.new_node_type = new_node_type
        self.title = title
    
    @abc.abstractmethod
    def parse_args(self, re_res):
        """Return new node constructor tuple from RE result
        
        Returns:
            tuple. Will be sent as *args in the constructor of the new node
        """
        raise NotImplementedError()

    def convert(self, node, text):
        """Replace given node by a new node based and given text parsing.
        
        Args:
            node (docsido.Node): the nide to be replaced
            text (str): the text to be parsed for argument to new node
            
        Raises:
            docsido.DocsidoError: if text has illegal syntax 
        """
        re_res = self.regex.match(text)
        if re_res is None:
            raise DocsidoError('Invalid docsido %s syntax in line "%s"'
                                   % (self.title, text))
        args = self.parse_args(re_res)
        node.replace_by(self.new_node_type, *args)


class ParamNodeParser(BasicNodeParser):
    """Parse parameter type text.
    
    Parses parameter text that looks like `param_name (param_type): param_text`
    or `param_name: param_text`, and creates the node with arguments
    (param_name, param_type, param_text).
    """
    _REGEX = re.compile(r'(\*{0,2}\w+)\s*(\((%s)\))?\s*:\s*(\S.*)\s*' %
                        TYPE_REGEX)
    
    @property
    def regex(self):
        return self._REGEX
    
    def parse_args(self, re_res):
        param_name = re_res.group(1)
        param_type = re_res.group(3)
        param_text = re_res.group(4)
        return param_name, param_type, param_text


class OutputNodeParser(BasicNodeParser):
    """Parse output type text.
    
    Parses output text that looks like `output_type. output_text` or
    `output_text`, and creates the node with arguments
    (output_type, output_text).
    """
    _REGEX = re.compile(r'((%s)\.\s)?\s*(\S.*)\s*' % TYPE_REGEX)
    
    @property
    def regex(self):
        return self._REGEX
    
    def parse_args(self, re_res):
        out_type = re_res.group(2)
        out_text = re_res.group(3)
        return self.title, out_type, out_text


class ExceptNodeParser(BasicNodeParser):
    """Parse exception type text.
    
    Parses exception text that looks like `exception_type: exception_text` or
    `exception_type`, and creates the node with arguments
    (exception_type, exception_text).
    """
    _REGEX = re.compile(r'(%s)\s*(:\s*(\S.*))?\s*$' % TYPE_REGEX)
    
    @property
    def regex(self):
        return self._REGEX
    
    def parse_args(self, re_res):
        except_type = re_res.group(1)
        except_text = re_res.group(3)
        return except_type, except_text
