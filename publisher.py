# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 23:51:25 2019

@author: sejeong
"""

import paho.mqtt.publish as publish
import RPi.GPIO as GPIO
import numpy as np
import time
from random import *
mode=0#난이도

IRpin = 18#적외선 GPIO핀 
#ADC를 사용하기 위한 핀
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 9



Question = [InfraredRay,Button]#각각의 센서의 정보가 저장된 배열 

Answer = []#문제의 정답
#user = []#사용자의 정답 

def init():
    #초기
    GPIO.setmode(GPIO.BCM)
    
def initGPIO(pinnum, isIn):
    #pinnum은 핀번호
    #isIn은 input(True)용인지 output(False)용인지
    if(isIn):
        #만약 Input용이면
        GPIO.setup(pinnum,GPIO.IN)
    else:
        GPIO.setup(pinnum,GPIO.OUT)

def menuSelect():
    global mode
    while True:
        menu = int(input("1)쉬움 2)중간 3)어려움 4)종료 >>"))
        if menu !=4 :
#            publish.single("embedded/mqtt/project","PLAY",host="test.mosquitto.org")#mqtt서버에 연결
            mode = menu
            break
        elif menu == 4:
            #종료
            print("게임을 종료합니다...")
            break
        else:
            print("다시 선택")
        
def makeAnswer(size):
    #총 답의 size
    answer = []
    for i in range(0,size):
        answer.append(random())
        
    answer = np.array(answer) < 0.5
    return answer

def selectMenu(size):
    #사용할 센서의 종류를 선택한다
    #size만큼의 센서를 선택함 (0<size<=5)
    
def InfraredRay(size):
    #적외선센서
    global user
    global Answer
    initGPIO(IRpin,True)#IRPin을 GPIO.IN으로 설정한다 
    for i in range(size):
#        a = GPIO.input(IRpin)#적외선센서의 input값을 받아온다
        a = random() < 0.5
#        user.append(a)#사용자의 답을 저장한다
        time.sleep(1)#1초 뒤에 입력 값을 비교한다
        #사용자에게 1초의 텀이 주어진다
        if a == Answer[i]:
            print("■ ",end='')
        else:
            print("□ ",end='')

def Button(size):
    #버튼센서
    
    
def EASY():
    #easy모드로 게임을 실행한 경우
    #랜덤으로 3개를 고름
    pass
    
def NORMAL():
    #normal모드로 게임을 실행한 경우
    pass
    
def HARD():
    #hard모드로 게임을 실행한 경우 
    pass
    
if __name__ == '__main__':
#    menuSelect()#메뉴를 선택한다
   
    Answer = makeAnswer(mode+3)
    
#    InfraredRay(4)

    
        
