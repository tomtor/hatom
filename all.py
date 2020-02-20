import os
import socket
from datetime import datetime, timedelta
import requests
import time
import threading

import paho.mqtt.client as mqtt
import json

from influxdb import InfluxDBClient

from subprocess import call

os.environ["PATH"] = ".:" + os.environ["PATH"]

bPres="0.0"
bHumi="0.0"
bOut="0.0"
bIn="0.0"
bPower="0.0"

pressure= { }

for line in open("/home/tom/tmp/baro.dat"):
    sline= line.split(' ')
    pressure[int(sline[1].split(':')[0])]= float(sline[5])


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe('+/devices/+/up')

curt=0

#ifclient = InfluxDBClient('localhost', 8086, 'root', 'root', 'ttndb')
#ifclient = InfluxDBClient('pine64.v7f.eu', 8086, 'root', 'root', 'ttndb')
ifclient = InfluxDBClient('bsd.v7f.eu', 8086, 'root', 'root', 'ttndb')
#pineclient = InfluxDBClient('pine64.v7f.eu', 8086, 'root', 'root', 'ttndb')
def addFlux(node, m, v, ts= None):
    if ts == None:
        ts= datetime.now()
    epoch= int(ts.timestamp()*1000000000)
    json_body = [
        {
            "measurement": m,
            "tags": {
                "node": node
            },
            "time": epoch,
            "fields": {
                "value": v
            }
        }
    ]

    global ifclient
    try:
        ifclient.write_points(json_body)
    except:
        print('reconnect influxdb local')
        #ifclient = InfluxDBClient('localhost', 8086, 'root', 'root', 'ttndb')
        #ifclient = InfluxDBClient('pine64.v7f.eu', 8086, 'root', 'root', 'ttndb')
        ifclient = InfluxDBClient('bsd.v7f.eu', 8086, 'root', 'root', 'ttndb')

    #global pineclient
    #try:
        #pineclient.write_points(json_body)
    #except:
        #print('reconnect influxdb pine64')
        #pineclient = InfluxDBClient('pine64.v7f.eu', 8086, 'root', 'root', 'ttndb')

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global bPres, curt
    pl= json.loads(str(msg.payload,'utf-8'))
    d= pl['payload_fields']
    f = baro
    if pl['dev_id'] == 'stm-pcb-1' :
        f= stm
    elif pl['dev_id'] == 'stm-2' or pl['dev_id'] == 'stm-abp' :
        f= stm2
    elif pl['dev_id'] == 'stm-air-1' :
        f= stmair
    elif pl['dev_id'] == 'v7f-eu-mapper-1' :
        f = baro
    else :
        f = unknown
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), end=' ')
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file=f, end=' ')
    if f == stm :
        print('stm-1', d['batt'] + 100, d['temp'], d['pres'], flush=True)
        print('stm-1', (d['batt'] + 100)/100, d['temp'], d['pres'], file=f, flush=True)
        addFlux('stm-1', "voltage", (d['batt'] + 100)/100)
    elif f == stm2 :
        if d['batt'] >= 300 :
            d['batt'] = d['batt'] - 256
        print('stm-2', d['batt'] + 100, d['temp'], d['pres'], flush=True)
        print('stm-2', (d['batt'] + 100)/100, d['temp'], d['pres'], file=f, flush=True)
        addFlux('stm-2', "voltage", (d['batt'] + 100)/100)
        addFlux('stm-2', "temperature", float(d['temp']))
    elif f == stmair :
        d['temp']= round(10 * float(d['temp']),1)
        d['pres']= round((float(d['pres']) - 700) * 100,1)
        print('stm-air', d['batt'] + 100, d['temp'], d['pres'], d['itemp'], flush=True)
        print('stm-air', (d['batt'] + 100)/100, d['temp'], d['pres'], file=f, flush=True)
        addFlux('stm-air', "temperature", float(d['itemp'])-1.75)
        addFlux('stm-air', "voltage", (d['batt'] + 100)/100)
        addFlux('stm-air', "co2", d['temp'])
        addFlux('stm-air', "tvol", d['pres'])
    #elif pl['dev_id'] == 'brug-1' :
    elif 'brug-' in pl['dev_id'] :
        if pl['dev_id'] == 'brug-4' and d['batt'] >= 300 :
            d['batt'] = d['batt'] - 256
        d['temp']= round(10 * float(d['temp']),1)
        d['pres']= round((float(d['pres']) - 700) * 100,1)
        print(pl['dev_id'], d['batt'] + 100, d['temp'], d['pres'], d['itemp'], flush=True)
        addFlux(pl['dev_id'], "temperature", float(d['itemp'])-0.5)
        addFlux(pl['dev_id'], "voltage", (d['batt'] + 100)/100)
        addFlux(pl['dev_id'], "co2", d['temp'])
        addFlux(pl['dev_id'], "tvol", d['pres'])
    elif f == baro :
        if d['temp'] > 1000 :
          d['temp']= round(d['temp'] - 6553.6,1)
        print('mapper-1', d['batt'], d['temp'], d['pres'], flush=True)
        print('mapper-1', d['batt'], d['temp'], d['pres'], file=f, flush=True)
        addFlux('stm-baro', "temperature", float(d['temp']))
        addFlux('stm-baro', "pressure", float(d['pres']))
        bPres= str(round(d['pres'],1))
        curt= datetime.now().hour
        pressure[curt % 24]= d['pres']
    else :
        print('Unknown', flush=True)

def ttConnect():
    while True:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.username_pw_set('test-baarn', 'ttn-account-v2.CcYNF130aq1zhMJxtkRgLozhINLy1Hc93E088i8eIT8')
        try:
            client.connect("eu.thethings.network", 1883, 60)
            #client.loop_start()
            client.loop_forever()
            #while True:
                #client.loop()
        except:
            print('connect TTN failed')
        time.sleep(5)

tthr= threading.Thread(target=ttConnect)
tthr.daemon= True
tthr.start()

UDP_IP = "0.0.0.0"
UDP_PORT = 41234

buiten= open("/home/tom/tmp/buiten.dat", "a")
heater= open("/home/tom/tmp/heater.dat", "a")
power= open("/home/tom/tmp/power.dat", "a")
baro= open("/home/tom/tmp/baro.dat", "a")
stm= open("/home/tom/tmp/stm32.dat", "a")
stm2= open("/home/tom/tmp/stm32-2.dat", "a")
stmair= open("/home/tom/tmp/stm-air.dat", "a")

unknown= open("/dev/null", "a")

prevt= time.time()
prevcnt= 0

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

loop= 0

def blinkIt():
    global loop, curt
    #threading.Timer(18.0, blinkIt).start()

    while True:
        lm= loop % 6
        if lm == 0:
            call(["blink.py", bIn, "20", "0", "0" ])
            #call(["tft.py", bIn, "200", "0", "0", "0" ])
        elif lm == 1:
            call(["blink.py", bOut, "15", "20", "0" ])
            #call(["tft.py", bOut, "150", "200", "0", "25" ])
        elif lm == 2:
            call(["blink.py", bHumi, "10", "10", "40" ])
            #call(["tft.py", bHumi, "100", "50", "255", "50" ])
        elif lm == 3:
            call(["blink.py", bPres, "0", "20", "20" ])
            #call(["tft.py", bPres, "0", "200", "200", "75" ])
        elif lm == 4:
            call(["blink.py", bPower, "0", "20", "0" ])
            #call(["tft.py", bPower, "0", "200", "0", "100" ])
        elif lm == 5:
            bTime= datetime.now().strftime("%a %e %H:%M")
            call(["blink.py", bTime, "20", "20", "20" ])
            pressures= ""
            cur= datetime.now().hour
            if cur != curt:
                pressure[cur]= pressure.get(curt, 1000)
            x= 0
            for i in range(cur - 23, cur + 1) :
                pressures= (pressures + str(x) + ' '
                            + str(pressure.get(i % 24, 1000)) + ";")
                x= x + 1
            #pressures= pressures + str(x) + ' ' + str(pressure[curt])
            call(["tftimg", bIn, bOut, bHumi, bPres, bPower, pressures ])
            #call(["tft.py", bTime, "200", "200", "200", "140" ])
        #else:
            #call(["blink.py", "FIJNE KERST!", "40", "10", "10" ])
        loop= loop+1
        temp= open("/home/tom/public_html/public/temp.txt", "w")
        print("<span class=tempOut>", file=temp)
        print(bOut, "&deg;", file=temp)
        print("</span>", file=temp)
        print("</br>", file=temp)
        print("<span class=tempIn>", file=temp)
        print(bIn, "&deg;", file=temp)
        print("</span>", file=temp)
        print("</br>", file=temp)
        print("<span class=hydro>", file=temp)
        print(bHumi, "%", file=temp)
        print("</span>", file=temp)
        print("</br>", file=temp)
        print("<span class=pressure>", file=temp)
        print(bPres, file=temp)
        print("</span>", file=temp)
        print("</br>", file=temp)
        print("<span class=power>", file=temp)
        print(bPower, file=temp)
        print("</span>", file=temp)
        temp.close()

#blinkIt()
bthr= threading.Thread(target=blinkIt)
bthr.daemon= True
bthr.start()

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    v = data.decode("utf-8").split()
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), end=' ')
    Volt = v[2]
    if v[0] == '10110075' or v[0] == '2937704' :
        Temp = float(v[4])
        addFlux('esp-room', "temperature", Temp)
        bIn= str(Temp)
        Humi = float(v[6])
        bHumi= str(round(Humi,1))
        addFlux('esp-room', "humidity", Humi)
        OTemp = float(v[8])
        Volt = 75 + (1-int(v[2]))*3
        f = heater
        addFlux('esp-room', "heater", 1 - int(v[2]))
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file=f, end=' ')
        print(v[0], v[2], Volt, Temp, Humi, OTemp, addr, flush=True)
        print(v[0], v[2], Volt, Temp, Humi, OTemp, addr, file=f, flush=True)
    elif v[0] == '14791062' or v[0] == '2543320':
        Temp = float(v[4])
        Humi = float(v[6])
        OTemps = v[8].split('.')
        OTemp = float(OTemps[0])+float(OTemps[1])/10000
        addFlux('esp-1', "temperature", OTemp)
        bOut= str(round(OTemp,1))
        Volt = round(float(v[2])/146.1165,3)
        addFlux('esp-1', "voltage", Volt)
        f = buiten
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file=f, end=' ')
        print(v[0], v[2], Volt, Temp, Humi, OTemp, addr, flush=True)
        print(v[0], v[2], Volt, Temp, Humi, OTemp, addr, file=f, flush=True)
    elif v[0] == '210292' :
        t= time.time()
        if prevcnt == 0 :
            prevcnt= int(v[6]) - 1
        #kwatth= 3600/(t-prevt)/375 * (int(v[6]) - prevcnt)
        kwatth= 3600/(t-prevt)/1000 * (int(v[6]) - prevcnt)
        if kwatth > 20 :
            kwatth = 20
        prevcnt= int(v[6])
        prevt= t
        addFlux('power', "power", round(kwatth,3))
        f = power
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file=f, end=' ')
        print(v[0], round(kwatth,3), v[2], int(float(v[4])), v[6], addr, flush=True)
        print(v[0], round(kwatth,3), v[2], int(float(v[4])), v[6], addr, file=f, flush=True)
        bPower= str(round(kwatth,3))
    elif v[0] == '94678576' or v[0] == '967093808' :
        print(v[0], v[1], v[2], v[3])
        addFlux('esp-32', "voltage", float(v[2])/1000.0)
        #Humi = float(v[3])/10.0
        #OTemp = float(v[1])/10.0
        #addFlux('esp-32', "humidity", Humi)
        #addFlux('esp-32', "temperature", OTemp)
        ndata= int(v[4])
        diff= float(v[5])
        if ndata > 0 :
            tdiff= timedelta(seconds= diff / ndata)
            t= datetime.now() - timedelta(seconds= diff)
            for i in range(0, ndata) :
                t= t+tdiff
                print('  ', t, i, v[6+2*i], v[7+2*i])
                addFlux('esp-32', "temperature", float(v[6+2*i])/10.0, ts= t)
                addFlux('esp-32', "humidity", float(v[7+2*i])/10.0, ts= t)

    else :
        print(v[0], '?')
        f = unknown
    #requests.post('https://api.thingspeak.com/update.json', json= {'api_key':'HKK48KHC6JDMGP82','field1':Volt })
