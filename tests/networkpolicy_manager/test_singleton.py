#!/usr/bin/env python3
import pytest
from networkpolicy_manager.policy import Singleton

class TestSingleton():
    """
    make sure singleton class works appropriately
    """
    def test_singleton_is_none(self):
        context = Singleton.get_instance()
        assert context.get() == None

    def test_singleton_setter_function_works(self):
        context = Singleton.get_instance()
        context.set(True)
        assert context.get() == True

    def test_singleton_truly_behaves_like_a_singleton(self):
        context = Singleton.get_instance()
        context1 = Singleton.get_instance()
        context.set(True)
        assert context1.get() == True
