IP = '10.91.40.36'
PORT = 5000

import cv2
import numpy as np

import os
from os.path import join
import random

from socket import *
from getpass import getpass
import sys
import threading

from crowd_detector.detect import *

CHECK_CROWD_SLEEP = 1

class CrowdChecker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._sock = socket()
        print('ip = {} port = {}. Connecting...'.format(IP, PORT))
        self._sock.connect((IP, PORT))
        print('Connected.')
        self._lock = threading.Lock()
        self._curPeopleCount = 0
        self._isActive = False

    def run(self):
        print('Loading YOLO...')
        self._yolo = prepare_yolo(args['model_path'], class_names)
        print('YOLO loaded.')

        while 1:
            length = self._recvall(self._sock, 16)
            if length == None:
                break

            buf = self._recvall(self._sock, int(length))
            data = np.fromstring(buf, dtype='uint8')

            decimg = cv2.imdecode(data, 1)[:, :, ::-1]
            
            pred, person_count = predict_on_image(decimg, self._yolo, person_only=True)
            pred = np.asarray(pred, dtype='uint8')
            self._curPeopleCount = person_count
            print('Current people count: {}'.format(person_count))
            
            cv2.imshow('Client', pred[:, :, ::-1])
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self._sock.send('Quit'.encode("utf-8"))
                break
            else:
                self._sock.send('OK'.encode("utf-8"))

        self._sock.close()
        cv2.destroyAllWindows()

            # time.sleep(CHECK_CROWD_SLEEP)

    def isActive(self):
        self._lock.acquire()
        isActiveFlag = self._isActive
        self._lock.release()

        return isActiveFlag

    def howManyPeopleNow(self):
        self._lock.acquire()
        countPeople = self._curPeopleCount
        self._lock.release()

        return countPeople

    def _setActive(self, isActiveFlag):
        self._lock.acquire()
        self._isActive = isActiveFlag
        self._lock.release()

    def _recvall(self, conn, count):
        buf = b''
        while count:
            newbuf = conn.recv(count)
            if not newbuf:
                return None
            buf += newbuf
            count -= len(newbuf)

        return buf
