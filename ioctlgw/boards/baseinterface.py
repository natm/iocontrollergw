
import logging
import socket
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from multiprocessing import Queue
from ioctlgw.componentstate import ComponentState


DEFAULT_STATUS_INTERVAL = 60
DEFAULT_CONNECTION_TIMEOUT = 10
DEFAULT_CONNECTION_RECONNECT = 2

LOG = logging.getLogger(__name__)


class BaseInterface(threading.Thread):

    STATIC_RESPONSES = {
        "01050010ff008dff": ComponentState(component="digitaloutput", num=1, status="ON"),
        "010500100000cc0f": ComponentState(component="digitaloutput", num=1, status="OFF"),
        "01050011ff00dc3f": ComponentState(component="digitaloutput", num=2, status="ON"),
        "0105001100009dcf": ComponentState(component="digitaloutput", num=2, status="OFF"),
        "01050012ff002c3f": ComponentState(component="digitaloutput", num=3, status="ON"),
        "0105001200006dcf": ComponentState(component="digitaloutput", num=3, status="OFF"),
        "01050013ff007dff": ComponentState(component="digitaloutput", num=4, status="ON"),
        "0105001300003c0f": ComponentState(component="digitaloutput", num=4, status="OFF"),
        "01050014ff00cc3e": ComponentState(component="digitaloutput", num=5, status="ON"),
        "0105001400008dce": ComponentState(component="digitaloutput", num=5, status="OFF"),
        "01050015ff009dfe": ComponentState(component="digitaloutput", num=6, status="ON"),
        "010500150000dc0e": ComponentState(component="digitaloutput", num=6, status="OFF"),
        "01050016ff006dfe": ComponentState(component="digitaloutput", num=7, status="ON"),
        "0105001600002c0e": ComponentState(component="digitaloutput", num=7, status="OFF"),
        "01050017ff003c3e": ComponentState(component="digitaloutput", num=8, status="ON"),
        "0105001700007dce": ComponentState(component="digitaloutput", num=8, status="OFF")
    }
    STATIC_REQUESTS = {
        "01050010ff008dff": ComponentState(component="digitaloutput", num=1, status="ON"),
        "010500100000cc0f": ComponentState(component="digitaloutput", num=1, status="OFF"),
        "01050011ff00dc3f": ComponentState(component="digitaloutput", num=2, status="ON"),
        "0105001100009dcf": ComponentState(component="digitaloutput", num=2, status="OFF"),
        "01050012ff002c3f": ComponentState(component="digitaloutput", num=3, status="ON"),
        "0105001200006dcf": ComponentState(component="digitaloutput", num=3, status="OFF"),
        "01050013ff007dff": ComponentState(component="digitaloutput", num=4, status="ON"),
        "0105001300003c0f": ComponentState(component="digitaloutput", num=4, status="OFF"),
        "01050014ff00cc3e": ComponentState(component="digitaloutput", num=5, status="ON"),
        "0105001400008dce": ComponentState(component="digitaloutput", num=5, status="OFF"),
        "01050015ff009dfe": ComponentState(component="digitaloutput", num=6, status="ON"),
        "010500150000dc0e": ComponentState(component="digitaloutput", num=6, status="OFF"),
        "01050016ff006dfe": ComponentState(component="digitaloutput", num=7, status="ON"),
        "0105001600002c0e": ComponentState(component="digitaloutput", num=7, status="OFF"),
        "01050017ff003c3e": ComponentState(component="digitaloutput", num=8, status="ON"),
        "0105001700007dce": ComponentState(component="digitaloutput", num=8, status="OFF")
    }

    def __init__(self, name, address, connectionqueue, statusqueue, num_digital_outputs=0, num_digital_inputs=0):
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
        self.status = {
            "digitalinput": {},
            "digitaloutput": {}
        }
        self.num_digital_outputs = num_digital_outputs
        self.num_digital_inputs = num_digital_inputs

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
                # request digital input status
                dest.send(bytes.fromhex('01 01 00 00 00 08 3d cc'))
                data = dest.recv(8)
                self.process_response_packets(data=data)

                # request digital output status
                # dest.send(bytes.fromhex('01 01 00 10 00 08 3c 09'))
                # data = dest.recv(8)
                # self.process_response_packets(data=data)

                if self.requestqueue.empty() is False:
                    request = self.requestqueue.get()
                    for hex, state in self.STATIC_REQUESTS.items():
                        if request == state:
                            dest.send(bytes.fromhex(hex))
                            data = dest.recv(8)
                            self.process_response_packets(data=data)
                else:
                    time.sleep(0.1)
            except socket.error as e:
                LOG.warning("%s socket error %s reconnecting", self.name, e)
                dest = self.connect()

    def process_response_packets(self, data):
        h = data.hex()
        if h in self.STATIC_RESPONSES.keys():
            outcome = self.STATIC_RESPONSES[h]
            # LOG.info("%s packet response matched in static table", self.name)
            pin_changed = self.update_state(state=outcome)
            if pin_changed:
                self.push_status(component=outcome.component, num=outcome.num)
        elif h.startswith("010101"):
            # Handle DI 8 response.
            # TODO: also handle DO 8 way response
            do_hex = "%s%s" % (h[6], h[7])
            bits = str(bin(int(do_hex, 16)).zfill(8))
            y = self.bits_to_hash(bits=bits)
            for pin, status in y.items():
                pin_changed = self.update_state(ComponentState(component="digitalinput", num=pin+1, status=status))
                if pin_changed:
                    self.push_status(component="digitalinput", num=pin + 1)
            # Handle DO Control write single coil response
            pass

        else:
            LOG.warning("%s Response packets unexpected: %s", self.name, h)

    def request_digitaloutput(self, state):
        # called via MQTT
        self.requestqueue.put(state)

    def update_state(self, state):
        current_status = self.status[state.component].get(state.num, None)
        self.status[state.component][state.num] = state.status
        if current_status != state.status:
            return True
        else:
            return False

    def push_status(self, component=None, num=None):
        if component is None and num is None:
            for component in self.status.keys():
                for num, status in self.status[component].items():
                    self.statusqueue.put({"name": self.name, "state": ComponentState(component=component, num=num, status=status)})
        else:
            status = self.status[component][num]
            self.statusqueue.put({"name": self.name, "state": ComponentState(component=component, num=num, status=status)})

    def bits_to_hash(self, bits):
        h = {}
        for b in range(0, 8):
            if bits[7 - b] == "1":
                h[b] = "ON"
            else:
                h[b] = "OFF"
        return h