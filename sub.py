# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 23:44:34 2019

@author: hyoju
"""

import paho.mqtt.client as mqtt
from socket import gaierror
import threading
import time
import os

timer=None
def on_connect(client, userdata, flags, rc):
    print("pub-sub 연결")
    client.subscribe("embedded/mqtt/project")
    
def on_message(client,userdata,msg):
    global timerCheck
    print(str(msg.payload.decode("utf-8")))
    
    if str(msg.payload.decode("utf-8"))!="PLAY" and str(msg.payload.decode("utf-8"))!="STOP":
        #play와 stop이 아니면 chatting내용임
        print(str(msg.payload.decode("utf-8")))
    elif str(msg.payload.decode("utf-8"))=="STOP":
        #stop이면 돌고있는 스레드를 종료시킨다
        timer.stop()
    else:
        #play가 전달되면 타이머 스레드를 동작시킨다
        timer = MyTimer(nae="timer")
        timer.start()
        timer.join()#스레드가 종료할 때까지 대기

        
class MyTimer(threading.Thread):
    
    def ___init__(self):
        super(StoppableThread,self).__init__()
        self._stopp = threading.Event()
        #stop변수에 대해 이벤트 설정
        #stop을 한 경우 이미 사용되는 변수명이기 때문에 다른 변수명 사용
        
    def run(self):
        #타이머를 실행시킨다
        for i in range(180):
            #만약 check가 False이면 for문을 중지한다(중간에 중단된 것임)
            if self.check == False:
                break
            print(str(180-i)+"s")
            time.sleep(1)
            
            
    def stop(self):
        self._stopp.set()
        self.check = False
        #타이머 출력문을 멈추기 위해 check변수를 False로 세팅
    def stopped(self):
        return self._stopp.isSet()
            
        
if __name__=='__main__':
    try:
        while True:
            client = mqtt.Client()#client생성
            client.on_connect = on_connect#connect가 들어오면 실행시킬 함수
            client.on_message = on_message#message가 전달되면 실행시킬 함수
            client.connect("test.mosquitto.org",1883,60)#연결을 시도한다
            client.loop_forever()
    except KeyboardInterrupt:
        exit()
