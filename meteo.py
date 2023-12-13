#!/Library/Frameworks/Python.framework/Versions/3.6/bin/python3

from decouple import config
import json
import os
from urllib import request, error
import paho.mqtt.client as paho
import paho.mqtt.publish as publish
import pprint as pp
#from paho import mqtt
from math import exp

root_topic = 'weather'
mqtt_server = 'e4444600f9834ebe8e6502c4dbccbf68.s2.eu.hivemq.cloud'
user_pass = {'username': config('MQUSER'), 'password': config('MQPASS')}

def fmtMessage(topic, content):
   msg = {'topic': topic, 'payload': content, 'qos': 0, 'retain': False}
   return msg

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    #print("mid: " + str(mid))
    None

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def getRH(T, TD):
  RH = 100 * (exp((17.625 * TD)/(243.04 + TD))/exp((17.625 * T)/( 243.04 + T)))
  return RH

def formatMQData(temp, windspd, windir, station_id, station_name):
   message = {"temp": temp, "windspd": windspd, "winddir": windir, "station_id": station_id, "station_name": station_name}
   return json.dumps(message, ensure_ascii=False)

def convertDirection(direction):
   directionMap = {'Šiaurės': 0, 'Šiaurės rytų':45, 'Rytų':90, 'Pietryčių': 135, 'Pietų': 180, 'Pietvakarių': 225, 'Vakarų': 270, 'Šiaurės vakarų': 315}
   try:
      degrees = directionMap[direction]
   except:
      # Encode direction if no match found
      degrees = -1
   return degrees

url = 'https://eismoinfo.lt/weather-conditions-service'

session = request.urlopen(url)
data = str(session.read().decode(encoding='UTF-8'))
# print(session.info())
session.close()

js_data_kd = json.loads(data)
print('\nEismoinfo.lt:\n')

stationsList = []

for i in js_data_kd:
    stationData = formatMQData(i['oro_temperatura'], i['vejo_greitis_vidut'], convertDirection(i['vejo_kryptis']), i['id'], i['irenginys'])

    stationsList.append(fmtMessage(root_topic + '/' + i['id'], stationData))
    with open('stationdata/' + i['id'] + '.json', "w") as outfile:
        outfile.write(stationData)

publish.multiple(stationsList, hostname = mqtt_server, port = 8883, auth=user_pass, tls={'ca_certs': 'root-CA.crt'})

print(len(stationsList))

'''
url = 'http://www.hkk.gf.vu.lt/json.php'

try:
    session = request.urlopen(url)
    #print(session.info())
    data = str(session.read().decode(encoding='UTF-8'))
    session.close()
    data = data[4:-4]
    js_data_vu = json.loads(data)
    print('\nVU meteo:\n')
    print('Vilnius: %s C, %s m/s, %s %%' % (js_data_vu['zeno_AT_5s_C'],
    js_data_vu['zeno_Spd_5s_Kt'], js_data_vu['zeno_RH_5s']))
except error.URLError as err:
    print(err)
'''
