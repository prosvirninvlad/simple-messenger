class SuspendConnection(Exception): pass
class ClientAlreadyConnected(Exception): pass
class ClientAlreadyDisconnected(Exception): pass
class InvalidServerAddress(Exception): pass
class ServerDisconnected(Exception): pass
class SessionRunning(Exception): pass
class SessionAlreadyStopped(Exception): pass