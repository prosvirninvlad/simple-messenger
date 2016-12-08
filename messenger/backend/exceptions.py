class ServerException(Exception): pass
class ServerAlreadyRunning(ServerException): pass
class ServerAlreadyStopped(ServerException): pass
class ServerInvalidConfiguration(ServerException): pass
class SuspendSession(ServerException): pass
class CompanionDisconnected(ServerException): pass