#!/bin/python3
import paho.mqtt.client as mqtt, sys, json, yaml, ssl, os, time
from urllib.request import urlopen

leagueApiUri = "https://localhost:2999/liveclientdata/activeplayer"

####Read Config
with open("config.yaml","r") as stream:
  try:
    config = yaml.load(stream, Loader=yaml.SafeLoader)
  except:
    print("malformed config file")
    sys.exit()

####Connect to mqtt if defined
if config["mqtt"] != None:
  mqttConfig = config["mqtt"]
  mqttClient = mqtt.Client()
  if mqttConfig["username"] != None and mqttConfig["password"] != None:
    mqttClient.username_pw_set(mqttConfig["username"],mqttConfig["password"])
  try:
    mqttClient.connect("192.168.8.2")
  except:
    print("mqtt connection error")
    sys.exit()
  mqttTopics = mqttConfig["topics"]

####Start polling for the client data
while True:
  try:
    response = urlopen(leagueApiUri, context=ssl._create_unverified_context())
    responseData = json.loads(response.read().decode('utf-8'))
    stats = responseData["championStats"]
    maxHealth = int(stats["maxHealth"])
    currentHealth = int(stats["currentHealth"])
  except:
    time.sleep(5) ###server probably not up - don't hammer, wait 5 seocnds before retrying
    continue

  ###During load screen maxhealth = 0, so simply force to 100%
  if maxHealth != 0:
    healthPCT = currentHealth / maxHealth
  else:
    healthPCT = 1
  
  print(healthPCT)

  ###Get linear values
  if healthPCT > .5:
    red = 200*(1-healthPCT)
    green = 100
  else:
    red = 100
    green = 200*healthPCT
    
  ###Apply curve if desired
  if config["rgbcalc"] == "curve":
    red = pow((0.1598 * red),2)
    green = pow((0.1598 * green),2)

  ###round down
  red = str(int(red))
  green = str(int(green))

  print(red)
  print(green)

  ###dispatch to mqtt
  if config["mqtt"] != None:
    for topic in mqttTopics:
      mqttClient.publish(topic["path"],topic["template"].replace("$red",red).replace("$green",green))
  
  ###run commands
  if config["runcommand"] != None:
    for command in config["runcommand"]:
      os.system(command.replace("$red",red).replace("$green",green))

