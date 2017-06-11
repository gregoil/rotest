"""General, struct-like class."""
# pylint: disable=protected-access
from itertools import izip, chain


class BasicStruct(object):
    """Class for holding struct-like objects.

    Example:
        >>> class MyStruct(BasicStruct):
        ...     __slots__ = ('attr_a', 'attr_b')
        >>> MyStruct(5, attr_b=6)
        MyStruct(attr_a=5, attr_b=6)
    """

    __slots__ = ()  # should be extended by deriving classes

    def __init__(self, *args, **kwargs):
        """Initialize the struct.

        This sets the values of the fields (slots) according to the given
        arguments, or None if the value was not supplied.
        """
        for key, value in chain(izip(self.__slots__, args),
                                kwargs.iteritems()):
            setattr(self, key, value)

        for key in self.__slots__:
            if not hasattr(self, key):
                setattr(self, key, None)

    def __repr__(self):
        """Return a representation of the struct instance.

        Returns:
            str. representation of the struct.
        """
        attrs_str = ', '.join('%s=%r' % (key, getattr(self, key))
                              for key in self.__slots__)
        return '%s(%s)' % (self.__class__.__name__, attrs_str)

    def __cmp__(self, other):
        """Compare the values of the struct with another struct.

        If the struct types mismatch this method never returns 0 (equals).

        Args:
            other (object): other object to compare with.

        Returns:
            int. the comparison result (0 for equal).
        """
        if not isinstance(other, type(self)):
            # if the types are different we want to make sure the comparison
            # result is not 0, but remain consistent, so we compare the types
            return cmp(type(self), type(other))

        return cmp(self._to_tuple(), other._to_tuple())

    def __hash__(self):
        """Return a hash of the struct.

        Returns:
            int. hash value of the object.
        """
        return hash(self._to_tuple())

    def _to_tuple(self):
        """Return a tuple of the struct's values.

        Returns:
            tuple. tuple of the struct's values.
        """
        return tuple(getattr(self, key) for key in self.__slots__)

    def __getstate__(self):
        """Return the object's state. This is used for pickling.

        Returns:
            tuple. tuple representation of the struct's state.
        """
        return self._to_tuple()

    def __setstate__(self, state):
        """Load state from a given value. This is used for unpickling.

        Args:
            state (tuple): tuple representation of the state to load.
        """
        for key, value in izip(self.__slots__, state):
            setattr(self, key, value)
