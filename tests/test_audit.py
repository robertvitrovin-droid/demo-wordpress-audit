import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
from audit import jload


def test_jload_skips_php_notices():
    noisy = 'Deprecated: offsetGet(mixed [\\ReturnTypeWillChange]) in x.php\n[{"name":"akismet"}]'
    assert jload(noisy) == [{"name": "akismet"}]


def test_jload_empty():
    assert jload("no json here") == []
