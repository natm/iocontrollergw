
import logging
import socket
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from multiprocessing import Queue


DEFAULT_STATUS_INTERVAL = 10
DEFAULT_CONNECTION_TIMEOUT = 10
DEFAULT_CONNECTION_RECONNECT = 2

LOG = logging.getLogger(__name__)


class BaseInterface(threading.Thread):

    def __init__(self, name, address, connectionqueue, statusqueue, num_relays=0, num_digital_inputs=0):
        threading.Thread.__init__(self)
        self.name = name.strip().lower()
        self.connectionqueue = connectionqueue
        self.statusqueue = statusqueue
        self.requestqueue = Queue()
        self.host = address.split(":")[0]
        self.port = int(address.split(":")[1])
        self.state_di_current = None
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.push_status, 'interval', seconds=DEFAULT_STATUS_INTERVAL, jitter=2)
        self._connection_state = "disconnected"
        self._connection_count = 0

    def connect(self):
        while True:
            try:
                self._connection_state = "disconnected"
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                LOG.info("%s Connecting %s:%s", self.name, self.host, self.port)
                s.settimeout(DEFAULT_CONNECTION_TIMEOUT)
                s.connect((self.host, self.port))
                LOG.info("%s Connected", self.name)
                self._connection_state = "connected"
                self._connection_count += 1
                self.connectionqueue.put({"event": "connected", "name": self.name})
                return s
            except socket.error as e:
                LOG.warning("%s socket error %s reconnecting", self.name, e)
                self._connection_state = "disconnected"
                self.connectionqueue.put({"event": "disconnected", "name": self.name})
                time.sleep(DEFAULT_CONNECTION_RECONNECT)

    def run(self):
        self.scheduler.start()

        dest = self.connect()
        while True:
            try:
                dest.send(bytes.fromhex('01 01 00 00 00 08 3d cc'))
                data = dest.recv(8)
                h = data.hex()
                if h != self.state_di_current:
                    self.state_di_current = h
                    self.push_status()

                # LOG.info("%s %s", self.name, h)
                if self.requestqueue.empty() is False:
                    self.requestqueue.get()
                    # TODO: action request, e.g digitaloutput on/off
                time.sleep(0.1)
            except socket.error as e:
                LOG.warning("%s socket error %s reconnecting", self.name, e)
                dest = self.connect()

    def push_status(self):
        if self.state_di_current is not None:
            self.statusqueue.put({"name": self.name, "dicurrent": self.state_di_current})

    def status_update_output_relay(self, num, status):
        pass

    def status_update_input_digital(self, num, status):
        pass

    def full_update(self):
        LOG.info("Full update")
