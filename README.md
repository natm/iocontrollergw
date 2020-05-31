# I/O Controller gateway

Gateway for various protocol to/from multiple Chinese remote IO controllers (relays, digital input and output).

[![Build Status](https://travis-ci.org/natm/iocontrollergw.svg?branch=master)](https://travis-ci.org/natm/iocontrollergw)

Sensible interfaces provided for:

* MQTT (Home Assistant and NodeRed compatible)

#### Supported device status:

| Mfgr      | Part number  | Identifier       | Digital out | D in | A in | Description            | Status      |
|-----------|--------------|------------------|-------------|------|------|------------------------|-------------|
| HHC       | HHC-N-8I8O   | `hhc.hhc-n-8i8o` | 8 (relays)  |      | 8    | Bare board             | Development |
| Hi-Flying | HF6508       | `hiflying.hf6508`| 8 (relays)  | 8    | 8    | Semi industrial device | Development |

#### Config and deployment 

`config.yaml`:

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

Run it!

`docker run --init -d --name=iocontroller  /etc/myconfig.yaml:/config.yaml natm:/iocontrollergw:latest`

#### MQTT Topics

```
iocontroller/boards/cupboard1/connection                  connected | disconnected
iocontroller/boards/cupboard1/properties
iocontroller/boards/cupboard1/digitaloutput/1/status      ON
iocontroller/boards/cupboard1/digitaloutput/1/command     OFF
iocontroller/boards/cupboard1/digitalinput/1              ON
iocontroller/boards/cupboard1/digitalinput/1/command      OFF
iocontroller/status
```


#### Development

Local environment setup:

```
virtualenv -p python3 venv
source venv/bin/activate
pip3 install -r requirements.txt
./run.py -c my-config.taml
```

