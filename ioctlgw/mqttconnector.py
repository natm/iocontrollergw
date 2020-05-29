import logging
import json
import paho.mqtt.client as mqttc
from ioctlgw import version

LOG = logging.getLogger(__name__)


class MqttConnector(object):

    def __init__(self, service):
        self.service = service
        self.config = self.service.config
        self.mqtt_config = self.config["mqtt"]
        self.mqtt = mqttc.Client()
        self.mqtt_base_topic = self.mqtt_config["topic"]
        self.mqtt.on_connect = self.mqtt_on_connect
        self.mqtt.on_disconnect = self.mqtt_on_disconnect
        self.mqtt.on_message = self.mqtt_on_message
        self.mqtt.on_subscribe = self.mqtt_on_subscribe
        # MQTT status jobs

        self.service.scheduler.add_job(self.publish_status)
        self.service.scheduler.add_job(self.publish_status, 'interval', seconds=10, jitter=5)

    def start(self):
        # Start a background thread to maintain the MQTT connection
        LOG.info("MQTT Starting")
        if "user" in self.mqtt_config and "pass" in self.mqtt_config:
            self.mqtt.username_pw_set(self.mqtt_config["user"], self.mqtt_config["pass"])
        mqtt_host = self.mqtt_config["host"]
        mqtt_port = self.mqtt_config["port"]
        LOG.info("MQTT Connecting to %s:%s", mqtt_host, mqtt_port)
        self.mqtt.connect(mqtt_host, mqtt_port, 60)

        # Subscribe to interesting MQTT topics
        topics = [
            "/boards/+/digitaloutput/+/command"
        ]
        for topic_suffix in topics:
            self.mqtt.subscribe(f"{self.mqtt_base_topic}{topic_suffix}")

        self.mqtt.loop_start()

    def mqtt_on_connect(self, client, data, flags, rc):
        LOG.info("MQTT Connected %s", rc)

    def mqtt_on_disconnect(self, client, userdata, rc):
        if rc == 0:
            LOG.warning("Unexpected MQTT disconnection.")
        else:
            LOG.warning("Unexpected MQTT disconnection. Will auto-reconnect")

    def mqtt_on_subscribe(self, client, userdata, mid, gqos):
        LOG.info("MQTT Subscribed %s", mid)

    def mqtt_on_message(self, client, userdata, msg):
        LOG.info("MQTT Message %s %s", msg.topic, msg.payload)

    def mqtt_publish_message(self, suffix, payload, qos=0):
        topic = "%s/%s" % (self.mqtt_base_topic, suffix)
        self.mqtt.publish(topic=topic, payload=payload, qos=0)
        LOG.info("%s %s", topic, payload)

    def board_connection_event(self, name, event):
        self.mqtt_publish_message(suffix=f"boards/{name}/connection", payload=event)

    def board_io_event(self, name, msg):
        component = msg["component"]
        num = msg["num"]
        status = msg["status"]
        if status:
            payload = "ON"
        else:
            payload = "OFF"
        self.mqtt_publish_message(suffix=f"boards/{name}/{component}/{num}/status", payload=payload)

    def publish_status(self):
        status = {
            "uptime": self.service.uptime,
            "version": version()
        }
        self.mqtt_publish_message(suffix="status", payload=json.dumps(status))
