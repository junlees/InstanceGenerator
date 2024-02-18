import datetime
import os
import cv2
import firebase_admin
import threading
import json
import dlib
import numpy as np
import time
import argparse
from imutils import face_utils, resize
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import firestore
from scipy.spatial import distance

RIGHT_EYE = list(range(36, 42))
LEFT_EYE = list(range(42, 48))
MOUTH = list(range(48, 68))
NOSE = list(range(27, 36))
EYEBROWS = list(range(17, 27))
JAWLINE = list(range(1, 17))
ALL = list(range(0, 68))
EYES = list(range(36, 48))
EYEMOUTH = list(range(36, 68))

p = "shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(p)

def video():

    #print(args.arg)


    video_capture = cv2.VideoCapture(value_video+args.arg)
    video_capture.set(3, 480) #가로
    video_capture.set(4, 640) #세로
    fps = 10
    prev_time = 0
    
    # streaming_window_width = int(video_capture.get(3))
    # streaming_window_height = int(video_capture.get(4))
    count = 0

    
    while True:
        ret, frame = video_capture.read()
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        except:
            print('not found')
            connection(False)
            break
        
        rects = detector(gray, 0)
        current_time = time.time() - prev_time

        for (i, rect) in enumerate(rects):
            left = []
            right = []
            points = np.matrix([[p.x, p.y] for p in predictor(gray, rect).parts()])
            show_parts = points[EYES]
            for (i, point) in enumerate(show_parts):
                x = point[0,0]
                y = point[0,1]
                # print("x:",x)
                # print("y:",y)
                # print("i:",i)
                cv2.circle(frame, (x, y), 1, (0, 255, 255), -1)
                cv2.putText(frame, "{}".format(i + 1), (x, y - 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                if 0 <= i and i < 6:
                    left.append((x,y))
                if 6 <= i and i < 12:
                    right.append((x,y))
        
            # print("left:",left)
            # print("right:",right)
            left_ratio = calculate_EAR(left)
            right_ratio = calculate_EAR(right)
            avg = (left_ratio+right_ratio)/2
            avg = round(avg,2)
            count = count + 1
            if count == 10:
                dbUpdateThread = threading.Thread(target=dbUpdate, args=(left_ratio,right_ratio,avg, ))
                dbUpdateThread.start()
                count = 0


        if (ret is True) and (current_time > 1./ fps):
            prev_time = time.time()
            cv2.imshow('streaming video', frame)
            if cv2.waitKey(1) == ord('q'):
                break
        


    video_capture.release() 
    cv2.destroyAllWindows()
    

def dbUpdate(left, right, avg):
    print('left : %lf | right : %lf'%(left,right))
    dir.update({'left':left})
    dir.update({'right':right})
    dir.update({'avg':avg})
    print('Update Thread end-----------')

def connection(c):
    dir_connection.update({'chkConnectResponse':c})

def calculate_EAR(eye): # 눈 거리 계산
	A = distance.euclidean(eye[1], eye[5])
	B = distance.euclidean(eye[2], eye[4])
	C = distance.euclidean(eye[0], eye[3])
	ear_aspect_ratio = (A+B)/(2.0*C)
	return ear_aspect_ratio

with open('key/key.json') as keyFile:
    keyData = json.load(keyFile)
    value_certificate = keyData["certificate"]
    value_url = keyData["db_url"]
    value_video = keyData["video_url"]

cred = credentials.Certificate('key/'+value_certificate)
firebase_admin.initialize_app(cred, {'databaseURL':value_url})
#firebase_db = firestore.client()
parser = argparse.ArgumentParser()
parser.add_argument('arg')
args = parser.parse_args()

dir = db.reference('data/'+args.arg+'/ratio')  #realtime db
dir_connection = db.reference('users/'+args.arg)

connection(True)
video()

