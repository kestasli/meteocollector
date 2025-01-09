#!/Library/Frameworks/Python.framework/Versions/3.6/bin/python3
import time
from decouple import config
import json
import os
from urllib import request, error
from socket import timeout
from datetime import datetime
import paho.mqtt.client as paho
import paho.mqtt.publish as publish
import pprint as pp
#from paho import mqtt
from math import exp

start_time = time.time()

#scriptdir = '/Users/kestasli/Documents/pythonfun/MQTT_meteo/'
scriptdir = './'
root_topic = 'weather'
mqtt_server = 'e4444600f9834ebe8e6502c4dbccbf68.s2.eu.hivemq.cloud'
user_pass = {'username': config('MQUSER'), 'password': config('MQPASS')}
publishTopics = ['0000', '0310', '1187', '5351']

url_eismoinfo = 'https://eismoinfo.lt/weather-conditions-service'
url_vu = 'http://www.hkk.gf.vu.lt/ms_json.php'
stationsList = [] #stations data to be published in MQTT

def unifyID(name):
    #Set station ID to uniform format of 4 symbols
    maxlen = 4
    name = name.strip().replace(" ", "")
    filler = maxlen * '0'
    if maxlen >= len(name):
        return filler[0:(maxlen - len(name))] + name
    else:
        return name

def fmtMessage(topic, content):
   #This will create message with multiple topicks and messages to be published in one shot.
   msg = {'topic': topic, 'payload': content, 'qos': 0, 'retain': False}
   return msg

def getRH(T, TD):
  RH = 100 * (exp((17.625 * TD)/(243.04 + TD))/exp((17.625 * T)/( 243.04 + T)))
  return RH

def formatMQData(temp, windspd, windir, station_id, station_name, collection_time):
   #This will format JSON message for publishing to the MQTT server
   # Negative numbers will be used as indicator that particular sensor is not gathering data
   if windspd == None: windspd = -1
   if temp == None: temp = -99
   if windir == None: windir = -1
   message = {"temp": float(temp), "spd": float(windspd), "dir": windir, "id": station_id, "name": station_name, "update": collection_time}
   return json.dumps(message, ensure_ascii=False)

def convertDirection(direction):
   directionMap = {'Šiaurės': 0, 'Šiaurės rytų':45, 'Rytų':90, 'Pietryčių': 135, 'Pietų': 180, 'Pietvakarių': 225, 'Vakarų': 270, 'Šiaurės vakarų': 315}
   try:
      degrees = directionMap[direction]
   except:
      # Encode direction as error if no match found
      degrees = -1
   return degrees

#--------------------------------KD data--------------------------------
try:
   req = request.Request(url_eismoinfo)
   #req.add_header('Referer', 'https://www.hkk.gf.vu.lt/vu_ms/')
   session = request.urlopen(req, timeout = 3)
   data = str(session.read().decode(encoding='UTF-8'))
   session.close()

   js_data_kd = json.loads(data)

   for i in js_data_kd:
      formattedID = unifyID(i['id'])
      stationData = formatMQData(i['oro_temperatura'], i['vejo_greitis_vidut'], convertDirection(i['vejo_kryptis']), formattedID, i['irenginys'], i['surinkimo_data'])

      stationsList.append(fmtMessage(root_topic + '/' + formattedID, stationData))
      #with open('stationdata/' + i['id'] + '.json', "w") as outfile:
      #    outfile.write(stationData)
except error.URLError as err:
    print('ERROR: URL ' + url_vu)
    print(err)
except json.JSONDecodeError as err:
   print('ERROR: JSON ' + url_vu)
   print(err)
except timeout as err:
    print('ERROR: Timeout ' + url_vu)
    print(err)

#--------------------------------VU data--------------------------------
try:
    formattedID = unifyID('0')
    collTime = datetime.now().strftime('%Y-%m-%d %H:%M') #Collection time is not supplied by the station, injecting now() time as collection time. Should be aligned with UTC?

    req = request.Request(url_vu)
    req.add_header('Referer', 'https://www.hkk.gf.vu.lt/vu_ms/') #does not respond if header is not specified
    session = request.urlopen(req, timeout = 3)
    data = str(session.read().decode(encoding='UTF-8'))
    session.close()

    data = data[4:-3] #remove crap from inproperly formated JSON response
    js_data_vu = json.loads(data)

    stationData = formatMQData(js_data_vu['zeno_AT_5s_C'], js_data_vu['zeno_Spd_5s_Kt'], int(js_data_vu['zeno_Dir_5s']), formattedID, 'VU Meteo Stotis', collTime)
    stationsList.append(fmtMessage(root_topic + '/' + formattedID, stationData))

    #with open('stationdata/' + '0' + '.json', "w") as outfile:
    #    outfile.write(stationData)

except Exception as err:
   print("ERROR: ", type(err).__name__)
   stationData = formatMQData(None, None, None, formattedID, 'VU Meteo Stotis', collTime)
   stationsList.append(fmtMessage(root_topic + '/' + formattedID, stationData))

'''
except error.URLError as err:
    print('ERROR: URL ' + url_vu)
    print(err)
except json.JSONDecodeError as err:
   print('ERROR: JSON ' + url_vu)
   print(err)
except timeout as err:
    print('ERROR: Timeout ' + url_vu)
    print(err)
    #logging.error('socket timed out - URL %s', url)
'''

publish.multiple(stationsList, hostname = mqtt_server, port = 8883, auth=user_pass, tls={'ca_certs': scriptdir + 'root-CA.crt'})

#-----------------------------------------------------------------------

for station in stationsList:
   #print(station['topic'])
   print(station['payload'])
#pp.pprint(stationsList[0])

print(len(stationsList))
print("--- %s seconds ---" % (time.time() - start_time))
