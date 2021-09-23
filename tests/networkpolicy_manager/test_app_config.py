#!/usr/bin/env python3
import pytest
from networkpolicy_manager.config import App


def test_getter():
    """
    test config getter function
    """
    assert App.config('LOGLEVEL') == 'INFO'

def test_setter():
    """
    test config setter
    """
    App.set('LOGLEVEL', 'test')
    assert App.config('LOGLEVEL') == 'test'

def test_setter_not_allowed():
    """
    make sure things you are not allowed to set raise the exception
    """
    with pytest.raises(NameError) as e_info:
        App.set('LOGFORMAT', 'test')
