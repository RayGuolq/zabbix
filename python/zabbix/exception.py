class NotImplementedException(Exception):
    def __init__(self):
        Exception.__init__(self, "Not implemented!")

class ResourceDoesnotExistException(Exception):
    def __init__(self):
        Exception.__init__(self, "Resource doesn't exist!")

class InvalidPacketException(Exception):
    def __init__(self, reason=""):
        if reason != "":
            Exception.__init__(self, "Invalid packet: %s!" % reason)
        else:
            Exception.__init__(self, "Invalid packet!")

class InvalidParameterException(Exception):
    def __init__(self, reason=""):
        if reason != "":
            Exception.__init__(self, "Invalid parameter: %s" % reason)
        else:
            Exception.__init__(self, "Invalid parameter")

class ZabbixException(Exception):
    def __init__(self, reason=""):
        self.reason = reason
        if reason != "":
            Exception.__init__(self, "Zabbix failure: %s" % reason)
        else:
            Exception.__init__(self, "Zabbix failure")
