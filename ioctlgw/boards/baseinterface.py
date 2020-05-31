
import logging
import socket
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from multiprocessing import Queue
from ioctlgw.componentstate import ComponentState


DEFAULT_STATUS_INTERVAL = 60
DEFAULT_CONNECTION_TIMEOUT = 5
DEFAULT_CONNECTION_RECONNECT = 2
DEFAULT_COMMAND_PAUSE = 0.1
DEFAULT_DO_ALL_CHECK = 5

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

    def __init__(self, name, address, service, num_digital_outputs=0, num_digital_inputs=0):
        threading.Thread.__init__(self)
        self.name = name.strip().lower()
        self.service = service
        self.requestqueue = Queue()
        self.address = address
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
                self.service.queue_boards_connection.put({"event": "connected", "name": self.name})
                return s
            except socket.error as e:
                LOG.warning("%s socket error %s reconnecting", self.name, e)
                self._connection_state = "disconnected"
                self.service.queue_boards_connection.put({"event": "disconnected", "name": self.name})
                time.sleep(DEFAULT_CONNECTION_RECONNECT)

    def run(self):
        self.scheduler.start()

        dest = self.connect()
        do_all_check_count = None
        while True:
            try:
                # request digital input status
                dest.send(bytes.fromhex('01 01 00 00 00 08 3d cc'))
                data = dest.recv(8)
                self.process_response_packets(data=data, response_to="read_di_status_all")

                if do_all_check_count is None or int(do_all_check_count * DEFAULT_COMMAND_PAUSE) >= DEFAULT_DO_ALL_CHECK:
                    # request digital output status
                    dest.send(bytes.fromhex('01 01 00 10 00 08 3c 09'))
                    data = dest.recv(8)
                    self.process_response_packets(data=data, response_to="read_do_status_all")
                    do_all_check_count = 0

                if self.requestqueue.empty() is False:
                    request = self.requestqueue.get()
                    for hex, state in self.STATIC_REQUESTS.items():
                        if request == state:
                            dest.send(bytes.fromhex(hex))
                            data = dest.recv(8)
                            self.process_response_packets(data=data)
                else:
                    time.sleep(DEFAULT_COMMAND_PAUSE)
                    do_all_check_count += 1
            except socket.error as e:
                LOG.warning("%s socket error %s reconnecting", self.name, e)
                dest = self.connect()

    def process_response_packets(self, data, response_to=None):
        h = data.hex()
        if h in self.STATIC_RESPONSES.keys():
            outcome = self.STATIC_RESPONSES[h]
            # LOG.info("%s packet response matched in static table", self.name)
            pin_changed = self.update_state(state=outcome)
            if pin_changed:
                self.push_status(component=outcome.component, num=outcome.num)
        elif h.startswith("010101"):
            # Handle DI / DO responses.
            if response_to is None:
                LOG.warning("Unknown treble 01 response")
                return
            elif response_to == "read_di_status_all":
                component = "digitalinput"
            elif response_to == "read_do_status_all":
                component = "digitaloutput"

            do_hex = "%s%s" % (h[6], h[7])
            t = bin(int(do_hex, 16)).zfill(8)
            pins = self.bits_to_pins(bits=t)
            for pin, status in pins.items():
                pin_changed = self.update_state(ComponentState(component=component, num=pin, status=status))
                if pin_changed:
                    self.push_status(component=component, num=pin)
        else:
            LOG.warning("%s Response packets unexpected: %s", self.name, h)
        return

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
        if component is not None and num is not None:
            # individual component status
            status = self.status[component][num]
            self.service.queue_boards_io_status.put({"name": self.name, "state": ComponentState(component=component, num=num, status=status)})
        else:
            # all component status
            for component in self.status.keys():
                for num, status in self.status[component].items():
                    self.service.queue_boards_io_status.put({"name": self.name, "state": ComponentState(component=component, num=num, status=status)})
            # board status
            self.service.queue_boards_status.put({"name": self.name, "address": self.address})

    def bits_to_pins(self, bits):
        sbits = str(bits)
        h = {}
        for p in range(1, 9):
            h[p] = "OFF"
            if sbits[len(bits) - p] == "1":
                h[p] = "ON"
        return h

