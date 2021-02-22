import paho.mqtt.client as mqtt, sys, json, yaml, ssl, os, time
import urllib.request

#import requests

leagueApiUri = "https://127.0.0.1:2999/liveclientdata/activeplayer"

####Read Config
with open("config.yaml","r") as stream:
  try:
    config = yaml.load(stream, Loader=yaml.SafeLoader)
  except:
    print("malformed config file")
    sys.exit()

if "enable_keyb" in config:
  import usb.core
  import usb.backend.libusb1
  usb_device = usb.core.find(idVendor=0x048d, idProduct=0xce00, backend=usb.backend.libusb1.get_backend(find_library=lambda c: "c:\libusb\libusb-1.0.dll"))

def send_usb_col(red,green,blue):
  start =(0x14, 0x00)
  rgb = (red,green,blue)
  end = (0x00, 0x00)
  prog = 0x01
  speed = 0x0a
  bright = 0x32
  usb_device.ctrl_transfer(0x21,0x09,0x300,1,start + (0x01,) + rgb + end)
  usb_device.ctrl_transfer(0x21,0x09,0x300,1,start + (0x02,) + rgb + end)
  usb_device.ctrl_transfer(0x21,0x09,0x300,1,start + (0x03,) + rgb + end)
  usb_device.ctrl_transfer(0x21,0x09,0x300,1,start + (0x04,) + rgb + end)
  usb_device.ctrl_transfer(0x21,0x09,0x300,1,start + (0x05,) + rgb + end)
  usb_device.ctrl_transfer(0x21,0x09,0x300,1,start + (0x06,) + rgb + end)
  usb_device.ctrl_transfer(0x21,0x09,0x300,1,start + (0x07,) + rgb + end)
  usb_device.ctrl_transfer(0x21,0x09,0x300,1,(0x08, 0x02, prog, speed, bright, 0x08, 0x00, 0x00))

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
sslunverified = ssl._create_unverified_context()

while True:
  try:
    response = urllib.request.urlopen(leagueApiUri, context=sslunverified).read()
    responseData = json.loads(response)
    stats = responseData["championStats"]
    maxHealth = int(stats["maxHealth"])
    currentHealth = int(stats["currentHealth"])
  except Exception as e:
    print("Error - server probably not up")
    print(e)
    time.sleep(5) ###server probably not up - don't hammer, wait 5 seocnds before retrying
    continue

  ###During load screen maxhealth = 0, so simply force to 100%
  if maxHealth != 0:
    healthPCT = currentHealth / maxHealth
  else:
    healthPCT = 1
  
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
  healthPCT = str(round(healthPCT * 100))
  ired = int(red)
  igreen = int(green)
  red = str(ired)
  green = str(igreen)

  print("H:" + healthPCT + "  \tR:" + red + "  \tG:" + green + "  ") #, end="\r")

  ###dispatch to mqtt
  if "mqtt" in config and config["mqtt"] != None:
    for topic in mqttTopics:
      mqttClient.publish(topic["path"],topic["template"].replace("$red",red).replace("$green",green).replace("$health",healthPCT))
  
  ###run commands
  if "runcommand" in config and config["runcommand"] != None:
    for command in config["runcommand"]:
      os.system(command.replace("$red",red).replace("$green",green).replace("$health",healthPCT))

  if "enable_keyb" in config:
    send_usb_col(ired,igreen,0)

  time.sleep(0.05) #small wait to prevent carnage
