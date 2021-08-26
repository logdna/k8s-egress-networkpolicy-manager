#!/usr/bin/env python3
import pytest
from ipcurator.singleton import SourceIpTelemetry, Podlist

class TestSourceIpTelemetry():
    """
    make sure testsourceiptelemetry singleton class works appropriately
    """
    def test_singleton_is_none(self):
        context = SourceIpTelemetry.get_instance()
        assert context.get() == None

    def test_singleton_setter_function_works(self):
        context = SourceIpTelemetry.get_instance()
        context.set(True)
        assert context.get() == True

    def test_singleton_truly_behaves_like_a_singleton(self):
        context = SourceIpTelemetry.get_instance()
        context1 = SourceIpTelemetry.get_instance()
        context.set(True)
        assert context1.get() == True

class PodList():
    """
    make sure podlist singleton class works appropriately
    """
    def test_singleton_is_none(self):
        context = Podlist.get_instance()
        assert context.get() == None

    def test_singleton_setter_function_works(self):
        context = Podlist.get_instance()
        context.set(True)
        assert context.get() == True

    def test_singleton_truly_behaves_like_a_singleton(self):
        context = Podlist.get_instance()
        context1 = Podlist.get_instance()
        context.set(True)
        assert context1.get() == True
