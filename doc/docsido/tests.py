"""Docsido unit-tests."""
import unittest
from itertools import izip_longest

from converter import rewrite_autodoc
from rotest.common.colored_test_runner import colored_main


class ParseTest(unittest.TestCase):
    """Documentation parsing tests.
    
    All tests send a documentation examples to Docsido parser and compare
    the result with given expected result.
    """

    @staticmethod
    def get_lines(item):
        """Return item's docstring lines as sphinx does."""
        lines = item.__doc__.splitlines()
        # remove common indentation from all lines, except the first line
        # that is not indented.
        indent = min(len(line) - len(line.lstrip()) for line in lines[1:])
        if indent > 0:
            lines[1:] = [line[indent:] for line in lines[1:]]
        return lines

    @staticmethod
    def diff_str(actual_lines, expected_lines):
        """Returns nice string showing the difference between given lines."""
        result = ['actual / expected:']
        for actual, expected in izip_longest(actual_lines, expected_lines):
            if actual != expected:
                actual = 'act ' + repr(actual)
                expected = 'exp ' + repr(expected)
            result.append(actual)
            result.append(expected)
        return '\n'.join(result)

    def assert_lists(self, actual, expected):
        """Assert that given lists are equal."""
        self.assertEqual(actual, expected, self.diff_str(actual, expected))

    def run_test_on(self, source, expected, expected_errors=()):
        """Run Docsido on source docstring and compare to expected."""
        actual_errors = []
        expected_errors = list(expected_errors)
        def test_err_handler(text):
            actual_errors.append(text)
        lines = self.get_lines(source)
        expected_lines = self.get_lines(expected)[:-1]
        rewrite_autodoc(None, None, None, None, None, lines, test_err_handler)
        self.assert_lists(lines, expected_lines)
        self.assert_lists(actual_errors, expected_errors)

    def test_note(self):
        """Testing "Note" paragraph conversion."""
        def source():
            """Testing "note" paragraph.
            
            Note: one liner note.
            Note:
                one line note in other line.
                
            Note:
                very long multiline note with lots of words. So much that it
                does not fit in one line. It goes on to fill even another
                line.
            """
        def expected():
            """Testing "note" paragraph.
            
            .. note::
               one liner note.
            
            .. note::
               one line note in other line.
               
            .. note::
               very long multiline note with lots of words. So much that it
               does not fit in one line. It goes on to fill even another
               line.
               
            """
        self.run_test_on(source, expected)

    def test_warning(self):
        """Testing "Warning" paragraph conversion."""
        def source():
            """Testing "warning" paragraph.
            
            Warning: one liner warning.
            Warning:
                one line warning in other line.
                
            Warning:
                very long multiline warning with lots of words. So much that it
                does not fit in one line. It goes on to fill even another
                line.
            """
        def expected():
            """Testing "warning" paragraph.
            
            .. warning::
               one liner warning.
            
            .. warning::
               one line warning in other line.
               
            .. warning::
               very long multiline warning with lots of words. So much that it
               does not fit in one line. It goes on to fill even another
               line.
               
            """
        self.run_test_on(source, expected)

    def test_returns(self):
        """Testing "Returns" paragraph conversion."""
        def source():
            """Testing "returns" paragraph.
            
            Returns: return_type. one liner description
            Returns:
                return_type. one liner description of return value
            
            Returns:
                typeless one liner description of return value
            
            Returns:
                return_type. very long multiline description with lots of words,
                    so much that it does not fit in one line. It goes on to
                    fill even another line.
            
            Returns: return_type. very long multiline description with lots of
                words, so much that it does not fit in one line. It goes on to
                fill even another line.
            
            Returns:
            no return value error
            
            Returns:
                first return description
                illegal second return description
            """
        def expected():
            """Testing "returns" paragraph.
            
            :returns: :class:`return_type`. one liner description
            
            :returns: :class:`return_type`. one liner description of return value
            
            :returns: typeless one liner description of return value
            
            :returns: :class:`return_type`. very long multiline description with lots of words,
                  so much that it does not fit in one line. It goes on to
                  fill even another line.
                  
            :returns: :class:`return_type`. very long multiline description with lots of
               words, so much that it does not fit in one line. It goes on to
               fill even another line.
               
            Returns:
            no return value error
            
            Returns:
               first return description
               illegal second return description
            
            """
        errors = ['"returns" title without any value.',
                  'in line "illegal second return description": there should be'
                  ' only one "returns" value']
        self.run_test_on(source, expected, errors)

    def test_yields(self):
        """Testing "Yields" paragraph conversion."""
        def source():
            """Testing "yields" paragraph.
            
            Yields: return_type. one liner description
            Yields:
                return_type. one liner description of return value
            
            Yields:
                typeless one liner description of return value
            
            Yields:
                return_type. very long multiline description with lots of words,
                    so much that it does not fit in one line. It goes on to
                    fill even another line.
            
            Yields: return_type. very long multiline description with lots of
                words, so much that it does not fit in one line. It goes on to
                fill even another line.
                   
            Yields:
            no yield value error
            
            Yields:
                first yield description
                illegal second yield description
            """
        def expected():
            """Testing "yields" paragraph.
            
            :yields: :class:`return_type`. one liner description
            
            :yields: :class:`return_type`. one liner description of return value
            
            :yields: typeless one liner description of return value
            
            :yields: :class:`return_type`. very long multiline description with lots of words,
                  so much that it does not fit in one line. It goes on to
                  fill even another line.
                  
            :yields: :class:`return_type`. very long multiline description with lots of
               words, so much that it does not fit in one line. It goes on to
               fill even another line.
               
            Yields:
            no yield value error
            
            Yields:
               first yield description
               illegal second yield description
            
            """
        errors = ['"yields" title without any value.',
                  'in line "illegal second yield description": there should be'
                  ' only one "yields" value']
        self.run_test_on(source, expected, errors)

    def test_args(self):
        """Testing "Args" paragraph conversion."""
        def source():
            """Testing "args" paragraph.
            
            Args:
                par (par_type): one liner description of parameter
            
            Args:
                par: typeless one liner description of parameter
            
            Args:
                par (par_type): very long multiline description with lots of
                    words, so much that it does not fit in one line. It goes on
                    to fill even another line.
                    
            Args:
                par1 (par1_type): one liner description of parameter
                par2 (par2_type): very long multiline description with lots of
                    words, so much that it does not fit in one line. It goes on
                    to fill even another line.
                par3: typeless one liner description of parameter
                    
            Args: par1 (par1_type): one liner description of parameter
                par2 (par2_type): very long multiline description with lots of
                    words, so much that it does not fit in one line. It goes on
                    to fill even another line.
                par3: typeless one liner description of parameter
            
            Args:
                syntax_error
            
            Args:
                syntax_error: 
            """
        def expected():
            """Testing "args" paragraph.
            
            :param par: one liner description of parameter
            :type par: :class:`par_type`
            
            :param par: typeless one liner description of parameter
            
            :param par: very long multiline description with lots of
                  words, so much that it does not fit in one line. It goes on
                  to fill even another line.
                  
            :type par: :class:`par_type`
            
            :param par1: one liner description of parameter
            :type par1: :class:`par1_type`
            
            :param par2: very long multiline description with lots of
                  words, so much that it does not fit in one line. It goes on
                  to fill even another line.
            :type par2: :class:`par2_type`
            
            :param par3: typeless one liner description of parameter
            
            :param par1: one liner description of parameter
            :type par1: :class:`par1_type`
            
            :param par2: very long multiline description with lots of
                  words, so much that it does not fit in one line. It goes on
                  to fill even another line.
            :type par2: :class:`par2_type`
            
            :param par3: typeless one liner description of parameter
            
            Args:
               syntax_error
            Args:
               syntax_error: 
            
            """
        errors = ['Invalid docsido args syntax in line "syntax_error"',
                  'Invalid docsido args syntax in line "syntax_error: "']
        self.run_test_on(source, expected, errors)

    def test_raises(self):
        """Testing "Raises" paragraph conversion."""
        def source():
            """Testing "raises" paragraph.
            
            Raises:
                only_exception_type
            
            Raises:
                exception: one liner description of exception
            
            Raises:
                exception: very long multiline description with lots of words,
                    so much that it does not fit in one line.
            
            Raises:
                exception1: one liner description of exception
                exception2: very long multiline description with lots of words,
                    so much that it does not fit in one line.
                only_exception_type
            
            Raises: exception1: one liner description of exception
                exception2: very long multiline description with lots of words,
                    so much that it does not fit in one line.
                only_exception_type
            
            Raises:
                syntax error
            
            Raises:
                syntax_error: 
            """
        def expected():
            """Testing "raises" paragraph.
            
            :raises:
               :class:`only_exception_type`
            
            :raises:
               :class:`exception` - one liner description of exception
            
            :raises:
               :class:`exception` - very long multiline description with lots of words, so much that it does not fit in one line. 
            
            :raises:
               * :class:`exception1` - one liner description of exception
            
               * :class:`exception2` - very long multiline description with lots of words, so much that it does not fit in one line.
            
               * :class:`only_exception_type`
            
            :raises:
               * :class:`exception1` - one liner description of exception
            
               * :class:`exception2` - very long multiline description with lots of words, so much that it does not fit in one line.
            
               * :class:`only_exception_type`
            
            Raises:
               syntax error
            Raises:
               syntax_error: 
            
            """
        errors = ['Invalid docsido raises syntax in line "syntax error"',
                  'Invalid docsido raises syntax in line "syntax_error: "']
        self.run_test_on(source, expected, errors)

    def test_attributes(self):
        """Testing "Attributes" paragraph conversion."""
        class Source:
            """Testing "attributes" paragraph.
            
            Attributes:
                member (member_type): one liner description of member
            
            Attributes:
                member: typeless one liner description of member
            
            Attributes:
                member (member_type): very long multiline description with lots
                    of words, so much that it does not fit in one line.
            
            Attributes:
                member1 (member1_type): one liner description of member
                member2 (member2_type): very long multiline description with
                    lots of words, so much that it does not fit in one line.
                member3: typeless one liner description of member
            
            Attributes: member1 (member1_type): one liner description of member
                member2 (member2_type): very long multiline description with
                    lots of words, so much that it does not fit in one line.
                member3: typeless one liner description of member
            
            Attributes:
               syntax_error
            
            Attributes:
               syntax_error: 
            """
        class Expected:
            """Testing "attributes" paragraph.
            
            :attributes:
               **member** (:class:`member_type`) - one liner description of member
            
            :attributes:
               **member** - typeless one liner description of member
            
            :attributes:
               **member** (:class:`member_type`) - very long multiline description with lots of words, so much that it does not fit in one line. 
            
            :attributes:
               * **member1** (:class:`member1_type`) - one liner description of member
            
               * **member2** (:class:`member2_type`) - very long multiline description with lots of words, so much that it does not fit in one line.
            
               * **member3** - typeless one liner description of member
            
            :attributes:
               * **member1** (:class:`member1_type`) - one liner description of member
            
               * **member2** (:class:`member2_type`) - very long multiline description with lots of words, so much that it does not fit in one line.
            
               * **member3** - typeless one liner description of member
            
            Attributes:
               syntax_error
            Attributes:
               syntax_error: 
            
            """
        errors = [
              'Invalid docsido attributes syntax in line "syntax_error"',
              'Invalid docsido attributes syntax in line "syntax_error: "']
        self.run_test_on(Source, Expected, errors)

    def test_list(self):
        """Testing list paragraph conversion."""
        def source():
            """Testing "list" paragraph.
            
            * one liner
            * two liner
                the second line
            
            - two liner
                the second line
            - one liner
            
            #. two liner
                the second line
            #. two liner
                the second line
            """
        def expected():
            """Testing "list" paragraph.
            
            * one liner
            * two liner    the second line    
            
            - two liner    the second line
            - one liner
            
            #. two liner    the second line
            #. two liner    the second line    
            
            """
        self.run_test_on(source, expected)


if __name__ == '__main__':
    colored_main()
