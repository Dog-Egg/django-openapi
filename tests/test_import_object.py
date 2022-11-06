import pytest

from django_openapi.utils.functional import import_string


class ObjectA:
    class ObjectB:
        pass


def test_import_string():
    assert import_string('tests.test_import_object.ObjectA') is ObjectA
    assert import_string('.ObjectA', default_module='tests.test_import_object') is ObjectA
    assert import_string('tests.test_import_object:ObjectA') is ObjectA
    assert import_string('tests.test_import_object:ObjectA.ObjectB') is ObjectA.ObjectB
    assert import_string(':ObjectA.ObjectB', default_module='tests.test_import_object') is ObjectA.ObjectB

    with pytest.raises(ValueError, match='^Empty module name$'):
        assert import_string(':ObjectA.ObjectB')
