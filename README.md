# I/O Controller gateway

Gateway to/from multiple Chinese remote IO controllers (relays, digital input and output).

[![Build Status](https://travis-ci.org/natm/iocontrollergw.svg?branch=master)](https://travis-ci.org/natm/iocontrollergw)

Sensible interfaces provided for:

* MQTT (Home Assistant compatible)


Development setup:

```
virtualenv -p python3 venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Configuration:

```
iocontrollers:
  relay1:
    address: 192.168.0.11:8899
    board: hiflying.hf6508
  relay2:
    address: 192.168.0.12:8899
    board: hiflying.hf6508
  relay3:
    address: 192.168.0.13:902
    board: hhc.hhc-n-8i80
mqtt:
  server: my.mqtt.server
  username: x
  password: x
  topic: iocontroller
```

Running the app:

```
./run.py -c /etc/myconfig.yaml
```

Devices support status:

| Mfgr      | Part number  | Identifier       | Digital out | D in | A in | Description            | Status      |
|-----------|--------------|------------------|-------------|------|------|------------------------|-------------|
| HHC       | HHC-N-8I8O   | `hhc.hhc-n-8i8o` | 8 (relays)  |      | 8    | Bare board             | Development |
| Hi-Flying | HF6508       | `hiflying.hf6508`| 8 (relays)  | 8    | 8    | Semi industrial device | Development |


MQTT Topics

```
iocontroller/boards/cupboard1/connection                  connected | disconnected
iocontroller/boards/cupboard1/properties
iocontroller/boards/cupboard1/digitaloutput/1/status      ON
iocontroller/boards/cupboard1/digitaloutput/1/command     OFF
iocontroller/boards/cupboard1/digitalinput/1              ON
iocontroller/boards/cupboard1/digitalinput/1/command      OFF
iocontroller/status
```

Deployment

```
docker run --init -d --name="iocontroller"  /etc/iocontroller-config.yaml:/config.yaml natm:/iocontroller-gateway:stable
```
