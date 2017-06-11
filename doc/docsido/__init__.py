"""Docsido is an extension used to parse out doctrings.

It converts google convention docstring into restructured string used by
sphinx.

Parses function docstring with this structure:

def function(*args, **kwargs):
    '''One liner description of the function.    
    
    Long function description ...

    Args:
        name (type): description
        name (type): description
       
    Returns:
        type. description
       
    Yields:
        type. description
    
    Raises:
        exception_type: description
        exception_type: description
    '''


Parses class docstring with this structure:

class SampleClass(object):
    '''One liner description of the class.

    Long class description....

    Attributes:
        name (type): description.
        name (type): description.
    '''


Also parses:
    ''' Any object
    
    Note: description
    
    Warning: description
    
    '''
"""

from converter import rewrite_autodoc

def setup(app):
    """Setup Docsido expansion in Sphinx.
    
    Is called automatically by Sphinx when Docsido is used as expansion.
    
    Registers :func:`docsido.converter.rewrite_autodoc` as a handler for
    'autodoc-process-docstring' event. The handler will be called for each
    docstring Sphinx parses.
    
    Args:
        app: The Sphinx application object
    """
    app.connect('autodoc-process-docstring', rewrite_autodoc)
