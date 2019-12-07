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

mode=0#난이도
IRpin = 21#적외선 GPIO핀
ButtonPin = [17,27,22] #버튼 GPIO핀
LedPin = [5,6,13]#LED GPIO핀
PiezoPin = 12#부저 GPIO핀
GHPin = 18#조도 GPIO핀

    
#ADC를 사용하기 위한 핀
    
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 9
    
bus = smbus.SMBus(1)#i2c 인터페이스 디바이스 객체 생성
address = 0x68

Question = []
Bomb = []#폭탄을 해체했는지(True) 아닌지(False)
scale = [261,329,196]#도,미,솔
timer = None
clear = np.full(size,False)  

chatting = ''
chatTimer = None
chat_ok = True
#핀 세팅
def initSetting():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(IRpin,GPIO.IN)
    GPIO.setup(GHPin,GPIO.IN)
    GPIO.setup(ButtonPin[0],GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ButtonPin[1],GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ButtonPin[2],GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LedPin[0],GPIO.OUT)
    GPIO.setup(LedPin[1],GPIO.OUT)
    GPIO.setup(LedPin[2],GPIO.OUT)
    GPIO.setup(PiezoPin,GPIO.OUT)
    
        

def makeGame(size):
    #사용할 센서의 종류를 선택한다
    #size만큼의 센서를 선택함 (0<size<=5)
    global Bomb
    index = []
    game = []
    for i in range(size):
        while True:
            rand = randint(0,len(Question)-1)
            if (rand not in index):
                index.append(rand)
                game.append(Question[rand])
                Bomb.append(False)
                break
    return game

def clearSetting():
    GPIO.output(LedPin[0],GPIO.LOW)
    GPIO.output(LedPin[1],GPIO.LOW)
    GPIO.output(LedPin[2],GPIO.LOW)
    GPIO.output(PiezoPin,GPIO.OUT)
    
def menuSelect():
    global mode
    mode = randint(1,3)
    publish.single("embedded/mqtt/project","PLAY",hostname="test.mosquitto.org")#mqtt서버에 연결
        
def makeAnswer(size):
    #총 답의 size
    answer = []
    for i in range(0,size):
        answer.append(random())
        answer = np.array(answer) < 0.5
    return answer

def Chat():
    global chatTimer
    global chat_ok
    os.system('cls')
    print(">>설명하세요")
    chatTimer = threading.Timer(5,sendChat)#5초동안 설명할 수 있다
    while True:
        if chat_ok == False:
            break
        c = input()
        chatting += c
        
    
def sendChat():
    global chatTimer
    global chat_ok
    chat_ok = False
    publish.single("embedded/mqtt/project",chatting,hostname="test.mosquitto.org")#채팅내용을 보냄 
    chatting = ''
    chatTimer.cancel()
    chatTimer = None
    chat_ok = True
    os.system('cls')
    

#1.적외선센서
def InfraredRay(size):
    print("|||||기억하세요|||||")
    print("*1초씩 행동해주세요")
    
    if mode == 3:
        #조도 센서 output HIGH
        print("tip ) 가끔은 다른 센서의 도움을 받으세요")

    time.sleep(1)
    answer = makeAnswer(size)#사이즈만큼의 정답을 만든다
    for s in range(len(answer)):
        os.system('cls')
        if answer[s] == True:
            print("■ ",end='')
        else:
            print("□ ",end='')
        if mode == 1:
            time.sleep(0.8)
        elif mode == 2:
            time.sleep(0.5)
        else:
            time.sleep(0.3)
    user = []
    while True:
        Chat()
        for i in range(size):
            a = GPIO.input(IRpin)#적외선센서의 input값을 받아온다
            time.sleep(1)
            user.append(a)
            #문제를 푸는 사람이 입력한 값을 저장한다
        check = True
        for i in range(size): 
            if answer[i] == user[i]:
                #정답인 경우
                print("■ ",end='')
            else:
                #오답인 경우
                check = False
                print("□ ",end='')
            if(mode == 3):
                #어려움 난이도 일 때
                condition = GPIO.input(GHPin)#조도센서의 값을 가져온다
                set_condition = random()<random()#조도센서가 어떤 값을 가져야 하는지에 대한 조건
                #만약 조도센서의 조건도 만족시켜줘야함
                if condition != set_condition:
                    check=False
        if check:
            os.system('cls')
            print("|||||CLEAR|||||")
            time.sleep(1)
            break#모두 정답이므로 종료
    os.system('cls')
            
        
#2.MPU6050
def get_y_rotation(x,y,z):
    radians = math.atan2(x, dist(y,z))
    return -math.degrees(radians)

def get_x_rotation(x,y,z):
    radians = math.atan2(y, dist(x,z))
    return math.degrees(radians)

def read_word(adr):
    high = bus.read_byte_data(address,adr)
    low = bus.read_byte_data(address,adr+1)
    val = (high << 8) + low
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
    #Gyro/Acc 센서
    #i2c
    power_mgmt_1 = 0x6b
    #power_mgmt_2 = 0x6c
    address = 0x68
    bus.write_byte_data(address, power_mgmt_1, 0)
    #임의로 정답의 x, y값 지정(범위를 모르겠음_범위 수정 필요)
    #문제 예시 : x값을 100(random)이상으로 드시오
    answerX = randrange(1,180)
    answerY = randrange(1,180)
   
    #sub이 맞춰야할 조건을 pub에게 보여줌
    choice=["이상","이하"]  
    case1 = choice[randrange(0,2)]
    case2 = choice[randrange(0,2)]
    print("x값은 %f %s(으)로, y값은 %f %s(으)로 맞춰주십시오."% (answerX,case1,answerY,case2))
    #count=0#임시변수
    while True:
        
        Chat()
        #각속도(gyro) 데이터
        #gyro_xout = read_word_2c(0x43)
        #gyro_yout = read_word_2c(0x45)
        #gyro_zout = read_word_2c(0x47)
        
        #출력 확인용
        #print (\"gyro_xout: \", gyro_xout, \" scaled: \", (gyro_xout / 131))
        #print (\"gyro_yout: \", gyro_yout, \" scaled: \", (gyro_yout / 131))
        #print (\"gyro_zout: \", gyro_zout, \" scaled: \", (gyro_zout / 131))

        #가속도(acc) 데이터
        accel_xout = read_word_2c(0x3b)
        accel_yout = read_word_2c(0x3d)
        accel_zout = read_word_2c(0x3f)

        accel_xout_scaled = accel_xout / 16384.0
        accel_yout_scaled = accel_yout / 16384.0
        accel_zout_scaled = accel_zout / 16384.0

        #출력 확인용
        #print (\"accel_xout: \", accel_xout, \" scaled: \", accel_xout_scaled)
        #print (\"accel_yout: \", accel_yout, \" scaled: \", accel_yout_scaled)
        #print (\"accel_zout: \", accel_zout, \" scaled: \", accel_zout_scaled)

        #우리가 정답이랑 비교해봐야할 값인 것 같음
        xRotation = get_x_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)
        yRotation = get_y_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)
        #print (\"x rotation: \" , get_x_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled))
        #print (\"y rotation: \" , get_y_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled))
        print(xRotation, yRotation)
        time.sleep(1)
    
        if case1==0:
        #x이상
            if case2==0:
            #y이상
                if xRotation>answerX and yRotation>answerY:
                    print("■ ",end='')
                    break
            elif case2==1:
            #y이하
                if xRotation>answerX and yRotation<answerY:
                    print("■ ",end='')
                    break
        elif case1==1:
        #x이하
            if case2==0:
            #y이상
                if xRotation<answerX and yRotation>answerY:
                    print("■ ",end='')
                    break
            elif case2==1:
            #y이하
                if xRotation<answerX and yRotation<answerY:
                    print("■ ",end='')
                    break
                
            
#3.버튼센서
def Button(size):
    print("|||||보이지 않아도 해결할 수 있습니다|||||")
    answer = []
    button_on = [False,False,False]
    condition = False
    for i in range(size):
        index = randint(0,2)
        answer.append(randint(0,3)-1)
        button_on[index] = True 
    if mode ==1:
        print("tip ) %d개만 순서대로 1초씩 누르세요"%(np.count_nonzero(button_on)))
    while True:
        Chat()
        check = True
        for i in range(size):
            a = [GPIO.input(ButtonPin[0]),GPIO.input(ButtonPin[1]),GPIO.input(ButtonPin[2])]
            time.sleep(1)
            if mode == 1:
                #쉬움모드일 때
                if a[answer[index]] == 1:
                    print("■ ",end='')
                else:
                    check = False
                    print("□ ",end='')
            elif mode == 2:
                #중간모드일 때
                if a[answer[index]]==1:
                    check = False
                    print("□ ",end='')
                else:
                    print("■ ",end='')
            else:
                
        if check:
            os.system('cls')
            print("|||||CLEAR|||||")
            time.sleep(1)
            break
    os.system('cls')

#4.조도센서
def Goughness(size):
    #1과 0사이의 값으로 나옴
    
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
        answer_g = [randrange(0,1),randrange(0,1),randrange(0,1)]
        
        #자릿수만큼 답을 맞출때까지 while문
        while ans_count!=len(answer_g):
            Chat()
            #조도 센서 값 계속 읽어오기위해 무한루프
            while True:
                if GPIO.input(GHPin)==answer_g[ans_count]:
                    ans_count+=ans_count
                    print("%s번째 자리를 맞췄습니다.",ans_count)
                    break

    elif mode==2:
        #중간 난이도
        #정답 4자리
        
        ans_count=0;
        answer_g = [randrange(0,1),randrange(0,1),
                    randrange(0,1),randrange(0,1)]
        
        while ans_count!=len(answer_g):
            Chat()
            while True:
                if GPIO.input(GHPin)==answer_g[ans_count]:
                    ans_count+=ans_count
                    print("%s번째 자리를 맞췄습니다.",ans_count)
                    break
        
    else:
        #어려움 난이도
        #정답 6자리
        
        ans_count=0;
        answer_g = [randrange(0,1),randrange(0,1),randrange(0,1),
                    randrange(0,1),randrange(0,1),randrange(0,1)]
        
        while ans_count!=len(answer_g):
            Chat()
            while True:
                if GPIO.input(GHPin)==answer_g[ans_count]:
                    ans_count+=ans_count
                    print("%s번째 자리를 맞췄습니다.",ans_count)
                    break
    
#5.LED
def LED():
    #정답만큼 불킨다
    for i in range(len(clear)):
        if clear[i] == True:
            GPIO.output(LedPin,GPIO.HIGH)
    
#6.부저
def Piezo(size):
    #부저
    list = []
    for i in range(size):
        list.append(randint(0,len(scale)-1))
    return list


def playMusic(list):
    #부저 
    global scale
    p = GPIO.PWM(PiezoPin,100)
    p.start(100)
    p.ChangeDutyCycle(90)
    for i in range(len(list)):
        p.ChangeFrequency(scale[list[i]])
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
    #부저와 버튼으로 게임하기
    os.system("cls")
    print("|||||기억하세요|||||")
    list = Piezo(size)
    os.system("cls")
    while True:
        Chat()
        playMusic(list)
        check = True
        for i in range(size):
            os.system("cls"spd)
            a = [GPIO.input(ButtonPin[0]),GPIO.input(ButtonPin[1]),GPIO.input(ButtonPin[2])]
            a = [a.argmax()]
            playMusic(a)
            time.sleep(1)
            print("NEXT")
            if a[list[i]]!=1:
                check = False
            
        if check:
            break

#게임시작
def GameStart(size):
    global timer
    global clear
    game = makeGame(size)
    for i in range(size):
        game[i](size)
        clear[i] = True
        LED()
    if timer != None and sum(clear)==size:
        #시간 제한이 끝나기 전에 clear한 경우
        timer.cancel()#타이머를 멈춘다
        GameOver()
        
    
#게임Over(종료)
def GameOver():
    global timer
    os.system("cls")
    timer = None
    clearSetting()
    print("|||||GAME OVER|||||") 
    time.sleep(1)
    
if __name__ == '__main__':
    try:
        os.system('cls')#화면지우기
        initSetting()
        print("BOMBULATOR")
        print("모드 선택 중....")
        menuSelect()#메뉴를 선택한다
        time.sleep(1)
        Question = [InfraredRay,Button,MPU6050,Goughness,MusicGame]#각각의 센서의 정보가 저장된 배열
        print("모드 선택 완료!")
        print("||||| 게임을 시작합니다 |||||")
        time.sleep(1)
        timer = threading.Timer(90,GameOver)#90초 후에 GameOver함수실행(1분 30초)
        timer.start()
        os.system('cls')
        if mode == 1 and mode == 2:
            GameStart(3)
        else:
            GameStart(4)
        
    except KeyboardInterrupt:
        clearSetting()
        GPIO.cleanup()