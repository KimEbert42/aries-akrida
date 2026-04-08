from gevent import lock as gevent_lock
from settings import Settings


class PortManager:
    def __init__(self):
        self.lock = gevent_lock.BoundedSemaphore()
        self.ports = list(range(Settings.START_PORT, Settings.END_PORT))

    def get_port(self):
        self.lock.acquire()
        try:
            port = self.ports.pop(0)
            return port
        finally:
            self.lock.release()

    def return_port(self, port):
        self.lock.acquire()
        try:
            self.ports.append(port)
        finally:
            self.lock.release()


portmanager = PortManager()