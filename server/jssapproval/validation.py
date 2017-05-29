import re

def valid_uuid(string):
    """ Return True if <string> is a valid UUID
        False if not.
    """
    pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    if re.match(pattern, string):
        return True
    else:
        return False

def valid_uun(string):
    """ Return True if <string> is a valid UUN
        False if not.
    """
    pattern = re.compile(r'^[0-9a-zA-Z]{1,8}$')
    if re.match(pattern, string):
        return True
    else:
        return False
