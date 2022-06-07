# coding=utf-8
import paho.mqtt.publish as publish
import socket
import time
import json
from os import environ

##  this agent reads from the solarmax inverter socket and
## publishes the data to a mqtt broker

s0_ip = environ.get('S0_IP')
s0_port = environ.get('S0_PORT')

mqtt_broker_ip = environ.get('MQTT_BROKER_IP')
mqtt_broker_port = environ.get('MQTT_BROKER_PORT')
mqtt_broker_auth = environ.get('MQTT_BROKER_AUTH')
mqtt_inverter_topic = environ.get('MQTT_INVERTER_TOPIC')
mqtt_s0_topic = environ.get('MQTT_S0_TOPIC')

# Sys parameter

status_codes = {
    20000: "Keine Kommunikation",
    20008: "Netzbetrieb",
}


field_map_s0 = {

    "KYR": "Energy_Year",
    "KMT": "Energy_Month",
    "KDY": "Energy_Day",
    "KT0": "Energy_Total",

    "PIN": "Installed_Power",

    "PAC": "AC_Power",

    "DYR": "Year",
    "DMT": "Month",
    "DDY": "Day",
    "THR": "Hour",
    "TMI": "Minute",

    "TYP": "Type",

    "SYS": "status_Code",
    # TNF: "generated_frequency",
}

req_data = "{FB;01;!!|64:&&|$$$$}"

def build_request(map):
    """ build the request message """
    r = ""
    for i in map:
        r = r+";"+i
    r = r[1:]
    req = req_data.replace("&&",r)
    # replace xy in req with length of string in 2 count hex
    req = req.replace('!!',format(len(req),'02X'))
    # replace $$$$ with checksum
    req = req.replace('$$$$',checksum((req[1:])[:-5]))
   
    return req

def checksum(data):
    """ calculate the checksum for the message """
    sum = 0
    print(data)
    for c in data:
        sum = sum + ord(c)
    # return 4 count hex value with leading zero
    print(sum)
    return format(sum, '04X')

def publish_message(topic, data, ip, port, auth):
    """ publish the message to the mqtt broker
    --- accepts a JSON payload
    --- publishs to the """
    ## following line is for local broker
    # client.publish(topic, json.dumps(data))
    publish.single(topic, payload=json.dumps(data), hostname=ip, port=port, auth=auth, client_id="Energymeter",)
    print ('published: ' + json.dumps(data) + '\n' + 'to topic: ' + topic)
    return


def map_data(f, v):
    # Convert to useful Units

    if f == "SYS":
        if v in status_codes:
            return status_codes[v]
        else:
            return "Unknown Status Code"
    elif f == "PAC":
        return v/2
    else:
        return v

def convert_to_json(map, data):
    # Example data:
    #b'{01;FB;EA|64:PAC=1F0A;PD01=CB2;PD02=13BA;PDC=206C;CAC=CAF;KHR=3DB3;KYR=B7E;KLY=14AB;KMT=BE;KLM=387;KDY=110;KLD=C6;KT0=4933;UDC=B70;UD01=B70;UD02=EAB;UL1=956;UL2=956;UL3=951;IDC=4CA;IL1=23F;IL2=23C;IL3=23C;SAL=0;SYS=4E28,0;TKK=31|3883}'
    data_split = data.split(':')[1].split('|')[0].split(';')
    test_dict = {}
    for i in data_split:
        field = i.split('=')[0]
        if field == "SYS":
            # Cutoff the ",0" in SYS status
            value = int(i.split('=')[1].split(',')[0], 16)
        else:
            value = int(i.split('=')[1], 16)
        test_dict[field] = {
            "Value": map_data(field, value),
            "Description": map[field],
            "Raw Value": value,
            
            }
    print(test_dict)
    return test_dict

def connect_to_inverter(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((ip, port))
    except socket.error as e:
        print( 'Failed to create socket: Error code: ' + str(e))
        return
        # sys.exit()
    return s

def read_data(sock, request):
    print ('sending: ' + request)
    sock.send(bytes(request, 'utf-8'))
    data_received = False
    response = ''
    print ('waiting for response')
    while not data_received:
        buf = sock.recv(1024)
        print ('received: ' + str(buf))
        if len(buf) > 0:
            response = response + str(buf)
            data_received = True
    print ('received: ' + response)
    return response



def main():
    print ("starting...")
    req_data_s0 = build_request(map=field_map_s0)
    while True:
        try:
            s0_s = connect_to_inverter(ip= s0_ip, port= s0_port)
            print ("connected to inverter")
            data = read_data(s0_s, req_data_s0)
            json_data = convert_to_json(map=field_map_s0, data=data)
            publish_message(topic=mqtt_s0_topic, data=json_data, ip=mqtt_broker_ip, port=mqtt_broker_port, auth=mqtt_broker_auth)
            s0_s.close()
            time.sleep(10)

        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print (message)
            continue

main()