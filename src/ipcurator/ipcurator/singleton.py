#!/usr/bin/env python3
class AsnCache:
    """
    singleton instance storing the external and internal IP telemetry from daemonsets
    """
    __instance = None

    def __init__(self):
        """
        private constructor
        """
        if AsnCache.__instance is not None:
            raise Exception(
                "This class is a singleton, don't use parenthesis!")
        else:
            AsnCache.__instance = self
            self.data = None

    @staticmethod
    def get_instance():
        """
        return singleton instance
        """
        if AsnCache.__instance is None:
            AsnCache()
        return AsnCache.__instance

    def set(self, data):
        """
        set the current AsnCache
        """
        self.data = data

    def get(self):
        """
        return the current AsnCache
        """
        return self.data


class SmallCidrLastUpdate:
    """
    singleton instance storing the external and internal IP telemetry from daemonsets
    """
    __instance = None

    def __init__(self):
        """
        private constructor
        """
        if SmallCidrLastUpdate.__instance is not None:
            raise Exception(
                "This class is a singleton, don't use parenthesis!")
        else:
            SmallCidrLastUpdate.__instance = self
            self.data = None

    @staticmethod
    def get_instance():
        """
        return singleton instance
        """
        if SmallCidrLastUpdate.__instance is None:
            SmallCidrLastUpdate()
        return SmallCidrLastUpdate.__instance

    def set(self, data):
        """
        set the current SmallCidrLastUpdate
        """
        self.data = data

    def get(self):
        """
        return the current SmallCidrLastUpdate
        """
        return self.data


class SmallCidrMap:
    """
    singleton instance storing the external and internal IP telemetry from daemonsets
    """
    __instance = None

    def __init__(self):
        """
        private constructor
        """
        if SmallCidrMap.__instance is not None:
            raise Exception(
                "This class is a singleton, don't use parenthesis!")
        else:
            SmallCidrMap.__instance = self
            self.data = None

    @staticmethod
    def get_instance():
        """
        return singleton instance
        """
        if SmallCidrMap.__instance is None:
            SmallCidrMap()
        return SmallCidrMap.__instance

    def set(self, data):
        """
        set the current SmallCidrMap
        """
        self.data = data

    def get(self):
        """
        return the current SmallCidrMap
        """
        return self.data


class SourceIpTelemetry:
    """
    singleton instance storing the external and internal IP telemetry from daemonsets
    """
    __instance = None

    def __init__(self):
        """
        private constructor
        """
        if SourceIpTelemetry.__instance is not None:
            raise Exception(
                "This class is a singleton, don't use parenthesis!")
        else:
            SourceIpTelemetry.__instance = self
            self.data = None

    @staticmethod
    def get_instance():
        """
        return singleton instance
        """
        if SourceIpTelemetry.__instance is None:
            SourceIpTelemetry()
        return SourceIpTelemetry.__instance

    def set(self, data):
        """
        set the current SourceIpTelemetry
        """
        self.data = data

    def get(self):
        """
        return the current SourceIpTelemetry
        """
        return self.data


class Podlist:
    """
    singleton instance storing the node list
    """
    __instance = None

    def __init__(self):
        """
        private constructor
        """
        if Podlist.__instance is not None:
            raise Exception(
                "This class is a singleton, don't use parenthesis!")
        else:
            Podlist.__instance = self
            self.data = None

    @staticmethod
    def get_instance():
        """
        return singleton instance
        """
        if Podlist.__instance is None:
            Podlist()
        return Podlist.__instance

    def set(self, data):
        """
        set the current Podlist
        """
        self.data = data

    def get(self):
        """
        return the current Podlist
        """
        return self.data
