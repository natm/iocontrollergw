#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import socket
import time
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from ioctlgw import version
from ioctlgw.boards import get_board
from ioctlgw.mqttconnector import MqttConnector
from ioctlgw.web import WebService

from multiprocessing import Queue

LOG = logging.getLogger(__name__)

class Service(object):

    def __init__(self, config):
        self.config = config
        self.startup = time.time()
        self.scheduler = BackgroundScheduler()
        self.controllers = {}
        self.mqtt = MqttConnector(service=self)
        self.connectionqueue = Queue()
        self.statusqueue = Queue()

    def start(self):

        #w = WebService(controllers=self.controllers)
        #w.start()

        LOG.info("Initialising boards")
        for name, controller in self.config["controllers"].items():
            address = controller["address"].strip().lower()
            identifier = controller["board"].strip().lower()
            LOG.info("Initialising '%s' using '%s' at '%s'", name, identifier, address)
            board = get_board(identifier=identifier)
            LOG.info("Found interface %s", board)
            # TODO: handle a miss identified board
            self.controllers[name] = board(name=name, address=address, connectionqueue=self.connectionqueue, statusqueue=self.statusqueue)

        LOG.info("Starting primary scheduler")
        self.scheduler.start()

        LOG.info("Starting MQTT")
        self.mqtt.start()

        LOG.info("Starting boards")
        for name, controller in self.controllers.items():
            LOG.info("Starting %s", name)
            self.controllers[name].start()
            # TODO: handle being unable to start a board

        while True:
            while self.statusqueue.empty() is False:
                event = self.statusqueue.get()
                self.mqtt.board_io_event(name=event["name"])
            while self.connectionqueue.empty() is False:
                event = self.connectionqueue.get()
                self.mqtt.board_connection_event( name=event["name"], event=event["event"])
            time.sleep(0.05)

    @property
    def uptime(self):
        return int((time.time()-self.startup)/60)


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('apscheduler.executors.default').propagate = False

    parser = argparse.ArgumentParser(description="IO Controller Gateway")
    parser.add_argument("-c", "--config", help="Config file", required=True)
    parser.add_argument("-v", "--verbose", help="Increase verbosity", action="store_true")
    args = parser.parse_args()

    LOG.info("IO Controller Gateway v%s", version())

    # check config exists
    cfgpath = args.config.strip()
    if os.path.isfile(cfgpath) is False:
        LOG.fatal("Specified config file does not exist: %s", cfgpath)
        sys.exit(1)

    # load the config
    with open(cfgpath, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

    s = Service(config=config)
    s.start()



    sys.exit(0)

if __name__ == "__main__":
    main()

