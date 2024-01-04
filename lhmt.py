import json
from urllib import request, error
from datetime import datetime, tzinfo
from pytz import timezone

def formatMQData(temp, windspd, windir, station_id, station_name, collection_time):
   #This will format JSON message for publishing to the MQTT server
   # Negative numbers will be used as indicator that particular sensor is not gathering data
   if windspd == None: windspd = -1
   if temp == None: temp = -99
   if windir == None: windir = -1
   message = {"temp": float(temp), "spd": float(windspd), "dir": windir, "id": station_id, "name": station_name, "update": collection_time}
   return json.dumps(message, ensure_ascii=False)

def getLocaltime(time):
    datetime_object = datetime.strptime(time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone('UTC'))
    return datetime_object.astimezone(timezone('Europe/Vilnius'))


#----------------------------------------------------------------------------
#Get list of available stations
url_lhmt_stations = 'https://api.meteo.lt/v1/stations'

try:
    req = request.Request(url_lhmt_stations)
    session = request.urlopen(req, timeout = 3)
    data = str(session.read().decode(encoding='UTF-8'))
    session.close()
    js_data_stations = json.loads(data)

    lhmt_stations = []
    for m in js_data_stations:
        lhmt_stations.append(m['code'])
    print(lhmt_stations)
    #Run through list of statuins and retrieve meteo data from each one
    for station in lhmt_stations:
        url_lhmt_stationdata = 'https://api.meteo.lt/v1/stations/' + station + '/observations/latest'
        req = request.Request(url_lhmt_stationdata)
        session = request.urlopen(req, timeout = 3)
        data = str(session.read().decode(encoding='UTF-8'))
        session.close()
        js_data_station = json.loads(data)

        station_id = station
        station_name = js_data_station['station']['name']
        #[-1] to grab last measure data
        temp = js_data_station['observations'][-1]['airTemperature']
        windspd = js_data_station['observations'][-1]['windSpeed']
        winddir = js_data_station['observations'][-1]['windDirection']
        localTime = getLocaltime(js_data_station['observations'][-1]['observationTimeUtc'])
        collection_time = localTime.strftime('%Y-%m-%d %H:%M')
        print(formatMQData(temp, windspd, winddir, station_id, station_name, collection_time))

except error.URLError as err:
    print('ERROR: URL ' + url_lhmt_stations)
    print(err)
except json.JSONDecodeError as err:
   print('ERROR: JSON ' + url_lhmt_stations)
   print(err)
except timeout as err:
    print('ERROR: Timeout ' + url_lhmt_stations)
    print(err)