# lol-lights
Small python script to monitor League Of Legends API and send Red/Green values to MQTT or a system command

## Deps:
paho-mqtt
(possibly others)

## Config:

Create a config.yaml file based on config.yaml.example
- mqtt is optional
- mqtt username/password are optional
- runcommand is optional
- rgbcalc is required - curve add a quadratic curve equation to R/G calculations, anything else results in the linear equation only

## Run:
`$ python lol-lights.py`
