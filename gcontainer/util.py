
def legal_name(name):
    """Check whether a given name is legal."""

    # must have at least one character
    if len(name) == 0:
        return False

    # must start with letter or number
    if not name[0].isalnum():
        return False

    # must not contain whitespace
    for c in name:
        if c.isspace():
            return False

    return True


def _sanitize(val):
    val = val.strip()
    if len(val) < 2:
        return val

    if val[0] == val[-1] and val[0] in "\"'":
        return val[1:-1]

    return val


def parse_environment(lines=[]):
    environment = {}
    for line in lines:
        line = line.strip()
        if len(line) == 0 or line[0] == '#':
            continue

        key, value = line.partition("=")[::2]
        key = _sanitize(key)
        value = _sanitize(value)

        if len(key) == 0:
            continue

        environment[key] = value

    return environment
