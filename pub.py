import paho.mqtt.publish as publish
import RPi.GPIO as GPIO
import numpy as np
import time
import random
from random import random,randrange,randint
import smbus #MPU6050에서 사용
import math
import threading
import os
import sys

mode=0#난이도
IRpin = 21#적외선 GPIO핀
ButtonPin = [17,27,22] #버튼 GPIO핀
ButtonOut = [7,8,25] #버튼 GPIO output설정 3.3 한번에되어서??
LedPin = [5,6,13]#LED GPIO핀
PiezoPin = 12#부저 GPIO핀
PiezoInputPin = 23#부저 input pin
GHPin = 18#조도 GPIO핀
toggle = False#함수별 종료 변수
    
#ADC를 사용하기 위한 핀
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 9
    
bus = smbus.SMBus(1)#i2c 인터페이스 디바이스 객체 생성
address = 0x68

Question = []#현재 선택된 문제를 담는 array
Bomb = []#폭탄을 해체했는지(True) 아닌지(False)
scale = [261,329,196]#도,미,솔
timer = None#timer스레드(시간제한)
clear = [False,False,False]#문제를 모두 해결했는지에 대한(총 3개의 문제에 대해)
user=[]
chatting = ''
chatTimer = None#설명 스레드
chat_ok = True#설명을 하는 중(True), 끝났는지(False)

ledOnIndex = 0#led에 불을 켜는 인덱스
#핀 세팅
def initSetting():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    #INPUT용은 GPIO.IN으로 세팅해주고, OUTPUT용은 GPIO.OUTPUT으로 세팅
    GPIO.setup(IRpin,GPIO.IN)
    GPIO.setup(GHPin,GPIO.IN)
    GPIO.setup(ButtonPin[0],GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ButtonPin[1],GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ButtonPin[2],GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LedPin[0],GPIO.OUT)
    GPIO.setup(LedPin[1],GPIO.OUT)
    GPIO.setup(LedPin[2],GPIO.OUT)
    GPIO.setup(PiezoPin,GPIO.OUT)
    GPIO.setup(PiezoInputPin,GPIO.OUT)
    #부저는 잔음이 남을 수 있기 때문에 OUTPUT설정 후 LOW로 세팅
    GPIO.output(PiezoInputPin,GPIO.LOW)
    GPIO.setup(ButtonOut[0], GPIO.OUT)
    GPIO.setup(ButtonOut[1], GPIO.OUT)
    GPIO.setup(ButtonOut[2], GPIO.OUT)
    #버튼에는 각각 LOW(버튼을 누르지 않은 상태에서 1, 누른 상태에서 0)
    GPIO.output(ButtonOut[0], GPIO.LOW)
    GPIO.output(ButtonOut[1], GPIO.LOW)
    GPIO.output(ButtonOut[2], GPIO.LOW)
        

def makeGame(size):
    #사용할 센서의 종류를 선택한다
    #size만큼의 센서를 선택함 (0<size<=5)
    global Bomb
    index = []
    game = []
    for i in range(size):
        while True:
            rand = randint(0,len(Question)-1)#random으로 int값을 선택
            if (rand not in index):
                #이미 선택된 index면 제외하고 새로운 index를 선택(중복제거)
                index.append(rand)
                game.append(Question[rand])
                Bomb.append(False)
                #선택된 인덱스의 문제를 해결해야하는 문제에 추가
                break
#     game.append(Question[4])
    return game

def clearSetting():
    #모든 세팅을 해제
    GPIO.output(LedPin[0],GPIO.LOW)
    GPIO.output(LedPin[1],GPIO.LOW)
    GPIO.output(LedPin[2],GPIO.LOW)
    GPIO.output(PiezoPin,GPIO.LOW)
    
def menuSelect():
    global mode
    mode = randint(1,3)
    #난이도를 랜덤으로 선택
    publish.single("embedded/mqtt/project","PLAY",hostname="test.mosquitto.org")
    #embedded/mqtt/project 토픽으로 접속을 시도
   
        
def makeAnswer(size):
    #총 답의 size
    #문제의 답을 랜덤으로 생성한다
    answer = []
    for i in range(0,size):
        answer = np.append(answer,random())
        answer = np.array(answer) < 0.5
    return answer

def Chat():
    #해결하는 사람에게 전달할 메세지를 입력하는 부분
    global chatTimer
    global chat_ok
    global chatting
    os.system('clear')
    print("▶ 설명하세요")
    chatTimer = threading.Timer(5,sendChat)#5초동안 설명할 수 있다(5초뒤 입력을 하지못하게)
    chatTimer.start()
    while True:
        c = input()
        if chat_ok == False:
            chat_ok = True
            break
        publish.single("embedded/mqtt/project",chatting,hostname="test.mosquitto.org")#채팅내용을 보냄 
        #chatting += c
    
    #전달이 끝나면 3초의 대기시간을 준다
    for i in range(3):
        print(3-i)
        time.sleep(1)
        
    
def sendChat():
    global chatTimer
    global chat_ok
    global chatting
    chat_ok = False#더이상 입력할 수 없게 False
    chatting = ''
    chatTimer.cancel()#타이머의 작동을 멈춘다
    chatTimer = None#타이머 변수를 다시 비워준다
    #publish.single("embedded/mqtt/project",chatting,hostname="test.mosquitto.org")#채팅내용을 보냄 
    os.system('clear')
    print("▶ ENTER 키를 누르면 시작합니다")
    

#1.적외선센서
def InfraredRay(size):
    global ledOnIndex
    global toggle
    global user

    print('██╗███╗   ██╗███████╗██████╗  █████╗ ██████╗ ███████╗██████╗ ')
    print('██║████╗  ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗')
    print('██║██╔██╗ ██║█████╗  ██████╔╝███████║██████╔╝█████╗  ██║  ██║')
    print('██║██║╚██╗██║██╔══╝  ██╔══██╗██╔══██║██╔══██╗██╔══╝  ██║  ██║')
    print('██║██║ ╚████║██║     ██║  ██║██║  ██║██║  ██║███████╗██████╔╝')
    print('╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ ')
    time.sleep(1)                                            
        
    answer = makeAnswer(size)#사이즈만큼의 정답을 만든다
    for s in range(len(answer)):
        os.system('clear')
        if answer[s] == True:
            print("OFF ",end='')#안가린거 1
        else:
            print("ON ",end='')#가린거 0
        if mode == 1:
            time.sleep(0.8)
        elif mode == 2:
            time.sleep(0.5)
        else:
            time.sleep(0.3)
    print()
    time.sleep(1)
    
    #user=[2,2,2,2]
    
    while True:
        #만약 게임이 종료된 상태면 exit
        if toggle==True:
            sys.exit(0)
        Chat()#설명하는 함수 호출
        
        check = True#해결했는지 아닌지 체크변수
        for i in range(size):
            a = GPIO.input(IRpin)#적외선센서의 input값을 받아온다
            time.sleep(1)
            #사용자의 입력에 따른 출력값
            if a==0:
                print("ON")
            else:
                print("OFF")
                
            if answer[i]==a:
                user[i]=a;
            else :
                user[i]=2
                
            time.sleep(1)
            #사용자가 입력한 답이 정답인지 오답인지 확인해준다
        for i in range(len(answer)):
            if answer[i]==user[i]:
                print("정답")
            else:
                #만약 오답이면 한번 더 문제를 해결하도록 한다
                check = False
                print("오답")
        time.sleep(1)
        #모두 정답인 경우        
        if check:
            GPIO.output(LedPin[ledOnIndex],GPIO.HIGH)
            ledOnIndex+=1
            #LED의 불을 하나 켠다
            gameClear()
            #CLEAR문구를 출력
            time.sleep(1)
            break#모두 정답이므로 종료
    os.system('clear')
            
        
#2.MPU6050
def get_y_rotation(x,y,z):
    #y의 회전값을 받아온다
    radians = math.atan2(x, dist(y,z))
    return -math.degrees(radians)

def get_x_rotation(x,y,z):
    #x의 회전값을 받아온다
    radians = math.atan2(y, dist(x,z))
    return math.degrees(radians)

def read_word(adr):
    high = bus.read_byte_data(address,adr)
    low = bus.read_byte_data(address,adr+1)
    val = (high << 8) + low
    #바이트 정보를 적어준다
    return val

def read_word_2c(adr):
    val = read_word(adr)
    if val>=0x8000:
        return -((65535-val)+1)
    else:
        return val

def dist(a,b):
    return math.sqrt((a*a)+(b*b))

def MPU6050(size):
    
    global ledOnIndex
    global toggle
    print('███╗   ███╗██████╗ ██╗   ██╗ ██████╗  ██████╗ ███████╗ ██████╗ ')
    print('████╗ ████║██╔══██╗██║   ██║██╔════╝ ██╔═████╗██╔════╝██╔═████╗')
    print('██╔████╔██║██████╔╝██║   ██║███████╗ ██║██╔██║███████╗██║██╔██║')
    print('██║╚██╔╝██║██╔═══╝ ██║   ██║██╔═══██╗████╔╝██║╚════██║████╔╝██║')
    print('██║ ╚═╝ ██║██║     ╚██████╔╝╚██████╔╝╚██████╔╝███████║╚██████╔╝')
    print('╚═╝     ╚═╝╚═╝      ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝ ╚═════╝ ')
                                                               
    
    #Gyro/Acc 센서
    #i2c
    power_mgmt_1 = 0x6b
    #power_mgmt_2 = 0x6c
    address = 0x68
    bus.write_byte_data(address, power_mgmt_1, 0)
    #임의로 정답의 x, y값 지정(범위를 모르겠음_범위 수정 필요)
    #문제 예시 : x값을 100(random)이상으로 드시오
    answerX = randrange(-20,50)
    answerY = randrange(-20,50)
   
    #sub이 맞춰야할 조건을 pub에게 보여줌
    choice=["이상","이하"]  
    case1 = choice[randint(0,1)]
    case2 = choice[randint(0,1)]
    
    print("x값은 %f %s(으)로, y값은 %f %s(으)로 맞춰주십시오."% (answerX,case1,answerY,case2))
    time.sleep(2)
    #count=0#임시변수
    while True:
        #만약 게임이 완전 종료가 된 경우 exit
        if toggle==True:
            sys.exit(0)
       # Chat()
        flag = False
        
        while True : 
            #게임이 완전 종료가 된 경우 exit
            if toggle==True:
                sys.exit(0)
            Chat()    
            #가속도(acc) 데이터
            accel_xout = read_word_2c(0x3b)
            accel_yout = read_word_2c(0x3d)
            accel_zout = read_word_2c(0x3f)

            accel_xout_scaled = accel_xout / 16384.0
            accel_yout_scaled = accel_yout / 16384.0
            accel_zout_scaled = accel_zout / 16384.0

            xRotation = get_x_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)
            yRotation = get_y_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)
               #센서의 값을 받아온다
            print(xRotation, yRotation)
            
            time.sleep(1)
               
                #정답 조건을 비교하는 부분
            if case1=="이상":
            #x이상
                if case2=="이상":
                #y이상
                    if xRotation>answerX and yRotation>answerY:
                        print("■ ",end='')
                        flag = True
                        break
                elif case2=="이하":
                #y이하
                    if xRotation>answerX and yRotation<answerY:
                        print("■ ",end='')
                        flag = True
                        break
            elif case1=="이하":
            #x이하
                if case2=="이상":
                #y이상
                    if xRotation<answerX and yRotation>answerY:
                        print("■ ",end='')
                        flag = True
                        break
                elif case2=="이하":
                #y이하
                    if xRotation<answerX and yRotation<answerY:
                        print("■ ",end='')
                        flag = True
                        break
        if flag==True:
            #만약 정답이면 LED를 하나 켜주고 clear문구 출력
            GPIO.output(LedPin[ledOnIndex],GPIO.HIGH)
            ledOnIndex+=1
            gameClear()
            time.sleep(1)
            break
    
    os.system('clear')
            
#3.버튼센서
def Button(size):
    
    global ledOnIndex
    global mode
    global toggle
    print('██████╗ ██╗   ██╗████████╗████████╗ ██████╗ ███╗   ██╗')
    print('██╔══██╗██║   ██║╚══██╔══╝╚══██╔══╝██╔═══██╗████╗  ██║')
    print('██████╔╝██║   ██║   ██║      ██║   ██║   ██║██╔██╗ ██║')
    print('██╔══██╗██║   ██║   ██║      ██║   ██║   ██║██║╚██╗██║')
    print('██████╔╝╚██████╔╝   ██║      ██║   ╚██████╔╝██║ ╚████║')
    print('╚═════╝  ╚═════╝    ╚═╝      ╚═╝    ╚═════╝ ╚═╝  ╚═══╝')
                     
    time.sleep(1)
    answer = []
    button_on = [False,False,False]
    #버튼이 눌렸는지에 대한 bool배열
    condition = False
    for i in range(size):
        index = randint(0,2)
        answer = np.append(answer,index)
        
        answer = answer.astype('int')
        
        button_on[index] = True 
        #정답을 random으로 만들어준다
        
    for i in range(size):
        print(str(answer[i])+" ",end='')
        #입력해야하는 답을 보여준다
    print()
        
    time.sleep(3)
    while True:
        if(toggle==True):
            sys.exit(0)
        Chat()
        #설명할 기회를 준다
        check = True
        #a = [GPIO.input(ButtonPin[0]),GPIO.input(ButtonPin[1]),GPIO.input(ButtonPin[2])]
        #print(a)
        
        for i in range(size):
            print("누르세요")
            a = [GPIO.input(ButtonPin[0]),GPIO.input(ButtonPin[1]),GPIO.input(ButtonPin[2])]
            time.sleep(2)
            #입력값을 받아 해당 값이 0(눌림)인지 확인한다
            #만약 정답 버튼의 값이 0이면 올바른 버튼이 눌린 것이므로 정답 아닌 경우 오답
            if int(a[int(answer[i])]) == 0:
                print("■ ",end='')
                print()
            else:
                check = False
                print("□ ",end='')
                print()
            time.sleep(2)
        
        os.system('clear')    
        if check:
            #만약 해결한 경우 LED불을 하나 켜주고 clear문구를 출력
            GPIO.output(LedPin[ledOnIndex],GPIO.HIGH)
            ledOnIndex+=1
            gameClear()
            time.sleep(1)
            break
    os.system('clear')

#4.조도센서
def Goughness(size):
    
    global ledOnIndex
    global toggle
    print('██╗     ██╗ ██████╗ ██╗  ██╗████████╗')
    print('██║     ██║██╔════╝ ██║  ██║╚══██╔══╝')
    print('██║     ██║██║  ███╗███████║   ██║   ')
    print('██║     ██║██║   ██║██╔══██║   ██║   ')
    print('███████╗██║╚██████╔╝██║  ██║   ██║   ')
    print('╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ')
    
    time.sleep(1)
    #데이터 출력 확인
    #while True:
        #print(GPIO.input(GHPin))
        #time.sleep(1)
        
    #빛을 비추면 1, 빛가리면 0
    #답으로 0과 1로 이루어진 네자리 숫자를 보여줌(정답)
    #조도센서를 사용하여 주어진 정답을 맞춰야함.
    global mode #난이도 값
    answer_g = [] #정답 초기화
    
    if mode==1:
        #쉬움 난이도
        #정답 3자리
        
        ans_count=0; #정답맞추면 1씩 증가하여 다음 자리 맞추도록 설정
        #정답 설정
        answer_g = [randint(0,1),randint(0,1),randint(0,1)]
        
        #자릿수만큼 답을 맞출때까지 while문
        while ans_count<len(answer_g):
            
            
            Chat()
            #조도 센서 값 계속 읽어오기위해 무한루프
            while True:
                if ans_count==len(answer_g):
                    break
                if(toggle==True):
                    sys.exit(0)
                ginput = GPIO.input(GHPin)
                #조도센서의 값을 받아온다
                time.sleep(1)
                if ginput==answer_g[ans_count]:
                    ans_count=ans_count+1
                    print("%s번째 자리를 맞췄습니다"%ans_count)
                else :
                    print("틀렸습니다")

    elif mode==2:
        #중간 난이도
        #정답 4자리
        
        ans_count=0;
        answer_g = [randint(0,1),randint(0,1),
                    randint(0,1),randint(0,1)]
        
        while ans_count<len(answer_g):
            Chat()
            while True:
                
                if(toggle==True):
                    sys.exit(0)
                if ans_count==len(answer_g):
                    break
                ginput = GPIO.input(GHPin)
                time.sleep(1)
                if ginput==answer_g[ans_count]:
                    ans_count=ans_count+1
                    print("%s번째 자리를 맞췄습니다"%ans_count)
                else :
                    print("틀렸습니다")
        
    else:
        #어려움 난이도
        #정답 6자리
        
        ans_count=0;
        answer_g = [randint(0,1),randint(0,1),randint(0,1),
                    randint(0,1),randint(0,1),randint(0,1)]
        
        while ans_count<len(answer_g):
            Chat()
            while True:
                if(toggle==True):
                    sys.exit(0)
                if ans_count==len(answer_g):
                    break
                ginput = GPIO.input(GHPin)
                time.sleep(1)
                if ginput==answer_g[ans_count]:
                    ans_count=ans_count+1
                    print("%s번째 자리를 맞췄습니다"%ans_count)
                else :
                    print("틀렸습니다")
    #문제를 해결한 경우 LED의 불을 하나 켜고 clear문구를 출력한다
    os.system("clear")
    GPIO.output(LedPin[ledOnIndex],GPIO.HIGH)
    ledOnIndex+=1
    gameClear()
    time.sleep(1)
    os.system('clear')
    
#6.부저
def Piezo(size):
    
    #부저의 정답을 만들어줍니다.(눌러야하는 순서)
    list = []
    for i in range(size):
        list.append(randint(0,len(scale)-1))
        print(list[i])
    return list


def playMusic(list):
    #부저 
    global scale
    name = ["도","미","솔"]
    GPIO.output(PiezoInputPin,GPIO.HIGH)
    p = GPIO.PWM(PiezoPin,100)
    p.start(100)
    p.ChangeDutyCycle(90)
    #부저에 소리가 날 수 있도록 output값을 설정합니다
    for i in range(len(list)):
        os.system("clear")
        #도,미,솔의 주기로 소리가 날 수 있도록 frequency를 조절합니다
        p.ChangeFrequency(scale[list[i]])
        print(name[list[i]])
        #각각의 난이도에 따라 소리가 나는 속도를 다르게 하기 위해 sleep에 다른 값을 줍니다
        if len(list) == 1:
            time.sleep(1)
        else:
            if mode == 1:
                time.sleep(1)
            elif mode == 2:
                time.sleep(0.5)
            else:
                time.sleep(0.3)
    p.stop()
    GPIO.output(PiezoPin,GPIO.LOW)
         
                          
def MusicGame(size):
    os.system("clear")
    global toggle
    global ledOnIndex
    print('███████╗ ██████╗ ██╗   ██╗███╗   ██╗██████╗ ')
    print('██╔════╝██╔═══██╗██║   ██║████╗  ██║██╔══██╗')
    print('███████╗██║   ██║██║   ██║██╔██╗ ██║██║  ██║')
    print('╚════██║██║   ██║██║   ██║██║╚██╗██║██║  ██║')
    print('███████║╚██████╔╝╚██████╔╝██║ ╚████║██████╔╝')
    print('╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ')
    #부저와 버튼으로 게임하기
    list = Piezo(size)
    #만든 정답을 list에 받아옵니다
    time.sleep(1)
    while True:
        
        playMusic(list)
        #정답을 한번 연주해줍니다
        Chat()
        #설명합니다
        check = True
        for i in range(size):
            a=[]
            while True:
                #게임이 완전 종료가된 경우 exit
                if toggle==True:
                    sys.exit(0)
                a = [GPIO.input(ButtonPin[0]),GPIO.input(ButtonPin[1]),GPIO.input(ButtonPin[2])]
                #버튼의 input값을 받아옵니다
                time.sleep(1)
                a = np.array(a)
                if 0 in a:
                    #버튼이 하나라도 눌릴 떄 까지 input을 계속 받습니다
                    #만약 눌린 버튼이 정답의 버튼과 일치하지 않는다면 check 변수를 false
                    if a[list[i]] != 0:
                        check = False
                    #0의 값을 가지는 index를 가져옵니다 (b)
                    b = [a.argmin()]
                    #b의 소리를 사용자에게 들려줍니다(자신이 현재 누른 버튼에 대한 소리)
                    playMusic(b)
                    break
        if check:
            #해결한 경우 LED의 불을 켜주고 clear문구를 출력합니다
            os.system("clear")
            GPIO.output(LedPin[ledOnIndex],GPIO.HIGH)
            ledOnIndex+=1
            gameClear()
            
            time.sleep(1)
            os.system('clear')
            break

#게임시작
def GameStart(size):
    global timer
    global clear
    game = makeGame(3)#랜덤으로 3개의 게임을 선택합니다
    for i in range(3):
        game[i](3)
        clear[i] = True#해결한 경우 clear변수를 True로 설정합니다
    if timer != None and sum(clear)==3:
        #시간 제한이 끝나기 전에 clear한 경우
        timer.cancel()#타이머를 멈춘다
        GameOver()
        
    
#게임Over(종료)
def GameOver():
    global timer
    global toggle
    toggle = True
    #게임이 끝났음을 toggle = True로 알립니다
    os.system("clear")
    timer = None
    clearSetting()
    
    print('  ▄████  ▄▄▄       ███▄ ▄███▓▓█████     ▒█████   ██▒   █▓▓█████  ██▀███  ')
    print(' ██▒ ▀█▒▒████▄    ▓██▒▀█▀ ██▒▓█   ▀    ▒██▒  ██▒▓██░   █▒▓█   ▀ ▓██ ▒ ██▒')
    print('▒██░▄▄▄░▒██  ▀█▄  ▓██    ▓██░▒███      ▒██░  ██▒ ▓██  █▒░▒███   ▓██ ░▄█ ▒')
    print('░▓█  ██▓░██▄▄▄▄██ ▒██    ▒██ ▒▓█  ▄    ▒██   ██░  ▒██ █░░▒▓█  ▄ ▒██▀▀█▄  ')
    print('░▒▓███▀▒ ▓█   ▓██▒▒██▒   ░██▒░▒████▒   ░ ████▓▒░   ▒▀█░  ░▒████▒░██▓ ▒██▒')
    print(' ░▒   ▒  ▒▒   ▓▒█░░ ▒░   ░  ░░░ ▒░ ░   ░ ▒░▒░▒░    ░ ▐░  ░░ ▒░ ░░ ▒▓ ░▒▓░')
    print('  ░   ░   ▒   ▒▒ ░░  ░      ░ ░ ░  ░     ░ ▒ ▒░    ░ ░░   ░ ░  ░  ░▒ ░ ▒░')
    print('░ ░   ░   ░   ▒   ░      ░      ░      ░ ░ ░ ▒       ░░     ░     ░░   ░ ')
    print('      ░       ░  ░       ░      ░  ░       ░ ░        ░     ░  ░   ░     ')
    print('                                                     ░           ')
    publish.single("embedded/mqtt/project","STOP",hostname="test.mosquitto.org")#게임이 끝났음을 sub에게도 알립니다
    time.sleep(100)#다른 스레드가 진행하지 않도록 sleep변수를 사용합니다
    sys.exit(0)#종료합니다
    
def gameClear():
    global ledOnIndex
    os.system("clear")
    print(' ________  ___       _______   ________  ________   ')  
    print('|\   ____\|\  \     |\  ___ \ |\   __  \|\   __  \    ')
    print('\ \  \___|\ \  \    \ \   __/|\ \  \|\  \ \  \|\  \   ')
    print(' \ \  \    \ \  \    \ \  \_|/_\ \   __  \ \   _  _\  ')
    print('  \ \  \____\ \  \____\ \  \_|\ \ \  \ \  \ \  \\  \| ')
    print('   \ \_______\ \_______\ \_______\ \__\ \__\ \__\\ _\ ')
    print('    \|_______|\|_______|\|_______|\|__|\|__|\|__|\|__|')
    if ledOnIndex >= 3:
        #문제를 모두 해결한 경우 
        time.sleep(1)
        os.system("clear")
        print('________  ________  _____ ______   ________  ___       _______  _________  _______   ___  ')     
        print('|\   ____\|\   __  \|\   _ \  _   \|\   __  \|\  \     |\  ___ \|\___   ___\\  ___ \ |\  \  ')    
        print('\ \  \___|\ \  \|\  \ \  \\\__\ \  \ \  \|\  \ \  \    \ \   __/\|___ \  \_\ \   __/|\ \  \   ')  
        print(' \ \  \    \ \  \\\  \ \  \\|__| \  \ \   ____\ \  \    \ \  \_|/__  \ \  \ \ \  \_|/_\ \  \    ')
        print('  \ \  \____\ \  \\\  \ \  \    \ \  \ \  \___|\ \  \____\ \  \_|\ \  \ \  \ \ \  \_|\ \ \__\   ')
        print('   \ \_______\ \_______\ \__\    \ \__\ \__\    \ \_______\ \_______\  \ \__\ \ \_______\|__|   ')
        print('    \|_______|\|_______|\|__|     \|__|\|__|     \|_______|\|_______|   \|__|  \|_______|   ___ ')
        print('                                                                                           |\__\ ')
        print('                                                                                           \|__|')
        publish.single("embedded/mqtt/project","STOP",hostname="test.mosquitto.org")
        #문제가 끝났음을 sub에게 알립니다
        time.sleep(3)
        sys.exit(0)
                                                      
    
if __name__ == '__main__':
    try:
        os.system('clear')#화면지우기
        #initSetting()
        #tmp()
        
        initSetting()#GPIO초기 설정
        #print("BOMBULATOR")

        print(' ________  ________  _____ ______   ________  ___  ___  ___       ________  _________  ________  ________     ')
        print('|\   __  \|\   __  \|\   _ \  _   \|\   __  \|\  \|\  \|\  \     |\   __  \|\___   ___\\   __  \|\   __  \    ')
        print('\ \  \|\ /\ \  \|\  \ \  \\\__\ \  \ \  \|\ /\ \  \\\  \ \  \    \ \  \|\  \|___ \  \_\ \  \|\  \ \  \|\  \   ')
        print(' \ \   __  \ \  \\\  \ \  \\|__| \  \ \   __  \ \  \\\  \ \  \    \ \   __  \   \ \  \ \ \  \\\  \ \   _  _\  ')
        print('  \ \  \|\  \ \  \\\  \ \  \    \ \  \ \  \|\  \ \  \\\  \ \  \____\ \  \ \  \   \ \  \ \ \  \\\  \ \  \\  \| ')
        print('   \ \_______\ \_______\ \__\    \ \__\ \_______\ \_______\ \_______\ \__\ \__\   \ \__\ \ \_______\ \__\\ _\ ')
        print('    \|_______|\|_______|\|__|     \|__|\|_______|\|_______|\|_______|\|__|\|__|    \|__|  \|_______|\|__|\|__|')

        print()
        print("모드 선택 중....")
        menuSelect()#메뉴를 선택한다
        print()
        input("▶ 아무키나 눌러 시작")
        
        Question = [InfraredRay,Button,MPU6050,Goughness,MusicGame]#각각의 센서의 정보가 저장된 배열
        print("모드 선택 완료")
        print()
        print("게임을 시작합니다") 
        print()
        time.sleep(1)
        timer = threading.Timer(180,GameOver)#180초 후에 GameOver함수실행(1분 30초)
        timer.start()
        os.system('clear')
        if mode == 1 and mode == 2:
            GameStart(3)
        else:
            GameStart(4)
        
    except KeyboardInterrupt:
        clearSetting()
        GPIO.cleanup()
