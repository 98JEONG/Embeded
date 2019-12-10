# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 23:44:34 2019

@author: hyoju
"""

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    client.subscribe("embedded/mqtt/project")
    
def on_message(client,userdata,msg):
    if str(msg.payload.decode("utf-8"))!="PLAY":
        #play가 아니면 chatting내용임
        print(str(msg.payload.decode("utf-8")))

if __name__=='__main__':
    try:
        while True:
            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect("test.mosquitto.org", 1883, 60)
            client.loop_forever()
    except KeyboardInterrupt:
        exit()
        
