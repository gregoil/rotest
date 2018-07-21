"""Test trimming utilities by filtering of tags."""
# pylint: disable=protected-access,eval-used
from fnmatch import fnmatch


VALID_LITERALS = ["and", "or", "not", "(", ")", "True", "False"]


def validate_boolean_expression(expression):
    """Validate an expression contains only boolean values and operators.

    The accepted literals are: "and", "or", "not", "(", ")", "True", "False".

    Args:
        expression (str): an expression to validate, e.g. "( True and False )".

    Raises:
        ValueError. in case the expression is not composed only of boolean
            values and operators.
    """
    for literal in expression.split():
        if literal not in VALID_LITERALS and literal != "":
            raise ValueError("Illegal boolean expression %r" % expression)


def match_tags(tags_list, tags_filter):
    """Check whether a tags list answers a condition expressed in tags_filter.

    Note:
        The tags are matched using fnmatch, which enables using filters such
        as 'Tag*'.

    Args:
        tags_list (iterable): tags list to be verified against the tags_filter,
            e.g. ["Tag1", "Tag2"].
        tags_filter (str): boolean expression composed of tags and boolean
            operators, e.g. "Tag1 and (Tag2 or Tag3 or Tag3)".

    Returns:
        bool. whether the tags list answers the condition expressed in the
            given tags_filter.

    Raises:
        ValueError. in case the given boolean expression is illegal.
    """
    spaced_expression = tags_filter.replace("(", " ( ").replace(")", " ) ")

    boolean_expression_list = []

    lower_case_tags = [tag.lower() for tag in tags_list]

    # Replace the tags in the expression with True if they appear in the tags
    # list, False otherwise.
    for element in spaced_expression.split():
        if element != "":
            if element not in VALID_LITERALS:
                element = str(any(fnmatch(tag, element.lower())
                                  for tag in lower_case_tags))

            boolean_expression_list.append(element)

    boolean_expression = " ".join(boolean_expression_list)

    # Validate that the calculated expression is comprised of boolean literals.
    validate_boolean_expression(boolean_expression)

    try:
        return eval(boolean_expression)

    except SyntaxError:
        raise ValueError("Illegal boolean expression %r" % tags_filter)
