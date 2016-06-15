from gcontainer.util import legal_name, parse_environment


def test_basic_name():
    assert legal_name("abc")
    assert legal_name("1234")
    assert legal_name("x")
    assert not legal_name("-abc")
    assert not legal_name(".abc")
    assert not legal_name("_abc")
    assert not legal_name("abc def")
    assert not legal_name("")


def _test_keys(lines, values):
    env = parse_environment(lines)
    assert len(env) == len(values)
    for key, val in values.iteritems():
        assert key in env
        assert env[key] == val


def test_parse_environment():
    assert len(parse_environment()) == 0
    assert len(parse_environment([])) == 0
    assert len(parse_environment(["", "     "])) == 0
    assert len(parse_environment(["# comment a", "    # comment b"])) == 0
    assert len(parse_environment(["\n", "     \n"])) == 0
    assert len(parse_environment(["# comment a\n", "    # comment b\n"])) == 0

    _test_keys(["key=value"], {"key": "value"})
    _test_keys([" key=value"], {"key": "value"})
    _test_keys(["key =value"], {"key": "value"})
    _test_keys([" key =value"], {"key": "value"})
    _test_keys(["key= value"], {"key": "value"})
    _test_keys([" key= value"], {"key": "value"})
    _test_keys(["key = value"], {"key": "value"})
    _test_keys([" key = value"], {"key": "value"})
    _test_keys(["key=value "], {"key": "value"})
    _test_keys([" key=value "], {"key": "value"})
    _test_keys(["key =value "], {"key": "value"})
    _test_keys([" key =value "], {"key": "value"})
    _test_keys(["key= value "], {"key": "value"})
    _test_keys([" key= value "], {"key": "value"})
    _test_keys(["key = value "], {"key": "value"})
    _test_keys([" key = value "], {"key": "value"})

    _test_keys(["key=value"], {"key": "value"})
    _test_keys(["'key'=value"], {"key": "value"})
    _test_keys(["\"key\"=value"], {"key": "value"})
    _test_keys(["key='value'"], {"key": "value"})
    _test_keys(["'key'='value'"], {"key": "value"})
    _test_keys(["\"key\"='value'"], {"key": "value"})
    _test_keys(["key=\"value\""], {"key": "value"})
    _test_keys(["'key'=\"value\""], {"key": "value"})
    _test_keys(["\"key\"=\"value\""], {"key": "value"})

    _test_keys(["key=value\n"], {"key": "value"})
    _test_keys(["\"key\"=\"value\"     \n"], {"key": "value"})

    _test_keys(["a=b\n", "foo = bar\n", "hello= world\n", "# a comment\n", "# bar=baz\n", "yes=\"another=value\"\n"],
               {'a': 'b', 'foo': 'bar', 'hello': 'world', 'yes': 'another=value'})
