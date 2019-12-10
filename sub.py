# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 23:44:34 2019

@author: hyoju
"""

import paho.mqtt.client as mqtt
from socket import gaierror
import threading
import time

timer=None
def on_connect(client, userdata, flags, rc):
    print("pub-sub 연결")
    client.subscribe("embedded/mqtt/project")
    
def on_message(client,userdata,msg):
    global timerCheck
    print(str(msg.payload.decode("utf-8")))
    
    if str(msg.payload.decode("utf-8"))!="PLAY" and str(msg.payload.decode("utf-8"))!="STOP":
        #play가 아니면 chatting내용임
        print(str(msg.payload.decode("utf-8")))
    elif str(msg.payload.decode("utf-8"))=="STOP":
        timer.stop()
    else:
        timer = MyTimer(nae="timer")
        timer.start()
        timer.join()

        
class MyTimer(threading.Thread):
    
    def ___init__(self):
        super(StoppableThread,self).__init__()
        self._stopp = threading.Event()
        
    def run(self):
        for i in range(180):
            if self.check == False:
                break
            print(str(180-i)+"s")
            time.sleep(1)
            
    def stop(self):
        self._stopp.set()
        self.check = False
    def stopped(self):
        return self._stop.isSet()
            
        
if __name__=='__main__':
    try:
        while True:
            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            try:
                client.connect("test.mosquitto.org",1883,60)
            except gaierror as e:
                print("Gauerror {}".format(e))
                time.sleep(1)
                restartlily()
            client.loop_forever()
    except KeyboardInterrupt:
        exit()
