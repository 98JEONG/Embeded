# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 00:53:33 2019

@author: hyoju
"""

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
import smbus #MPU6050에서 사용
mode=0#난이도

IRpin = 18#적외선 GPIO핀 
GApin = 20# MPU6050(Gyro/Acc 센서) GPIO

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
            

#아래 두 함수는 MPU6050에서 사         
def get_y_rotation(x,y,z):
    radians = math.atan2(x, dist(y,z))
    return -math.degrees(radians)

def get_x_rotation(x,y,z):
    radians = math.atan2(y, dist(x,z))
    return math.degrees(radians)
   
def MPU6050():
    #Gyro/Acc 센서
    
    #i2c
    power_mgmt_1 = 0x6b
    power_mgmt_2 = 0x6c
    
    bus = smbus.SMBus(1)#i2c 인터페이스 디바이스 객체 생성
    address = 0x68    
    bus.write_byte_data(address, power_mgmt_1, 0) #초기화?인거같던데 잘 모르겟음
    
    initGPIO(SMpin,False)#SMpin을 GPIO.OUT으로 설정 - 모터값을 pub이 확인
    
    p = GPIO.PWM(SMpin,50)
    p.start(7.5)
    
    #임의로 정답의 x, y값 지정(범위를 모르겠음_범위 수정 필요)
    #문제 예시 : x값을 100(random)이상으로 만드시오
    answerX = random.randrange(1,180);
    answerY = random.randrange(1,180);
    
    #sub이 맞춰야할 조건을 pub에게 보여줌
    choice=["이상","이하"]    
    print("x값은 %f %s(으)로, y값은 %f %s(으)로 맞춰주십시오.",
          answerX,
          case1 = choice[random.randrange(0,2)],
          answerY,
          case2 = choice[random.randrange(0,2)]);
          
    #각속도(gyro) 데이터
    gyro_xout = read_word_2c(0x43)
    gyro_yout = read_word_2c(0x45)
    gyro_zout = read_word_2c(0x47)
    #출력 확인용
    #print ("gyro_xout: ", gyro_xout, " scaled: ", (gyro_xout / 131))
    #print ("gyro_yout: ", gyro_yout, " scaled: ", (gyro_yout / 131))
    #print ("gyro_zout: ", gyro_zout, " scaled: ", (gyro_zout / 131))

    #가속도(acc) 데이터
    accel_xout = read_word_2c(0x3b)
    accel_yout = read_word_2c(0x3d)
    accel_zout = read_word_2c(0x3f)

    accel_xout_scaled = accel_xout / 16384.0
    accel_yout_scaled = accel_yout / 16384.0
    accel_zout_scaled = accel_zout / 16384.0
    #출력 확인용
    #print ("accel_xout: ", accel_xout, " scaled: ", accel_xout_scaled)
    #print ("accel_yout: ", accel_yout, " scaled: ", accel_yout_scaled)
    #print ("accel_zout: ", accel_zout, " scaled: ", accel_zout_scaled)

    #우리가 정답이랑 비교해봐야할 값인 것 같음
    xRotation = get_x_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)
    yRotation = get_y_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)
    #print ("x rotation: " , get_x_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled))
    #print ("y rotation: " , get_y_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled))
    
    #나는 여기까지인거 같아...
    if case1==0:
        #x이상
        if case2==0:
            #y이상
            if xRotation>answerX and yRotation>answerY:
                print("■ ",end='')
        elif case2==1:
            #y이하
            if xRotation>answerX and yRotation<answerY:
                print("■ ",end='')
    elif case1==1:
        #x이하
        if case2==0:
            #y이상
            if xRotation<answerX and yRotation>answerY:
                print("■ ",end='')
        elif case2==1:
            #y이하
            if xRotation<answerX and yRotation<answerY:
                print("■ ",end='')
    
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