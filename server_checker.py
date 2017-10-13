import paramiko
from paramiko import SSHException
import socket
import threading
import time

SSH_CONNECTION_TIMEOUT = 10     # seconds
CHECK_CONNECTION_SLEEP = 60
HOSTNAME='127.0.0.1'
PORT=31340
USERNAME='barbiturates'
PASSWORD='Griolud4'

class ServerChecker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._lock = threading.Lock()
        self._isActive = False

    def run(self):
        while 1:
            try:
                self._ssh.connect(hostname=HOSTNAME, port=PORT, username=USERNAME,
                    password=PASSWORD, timeout=SSH_CONNECTION_TIMEOUT)
                self._setActive(True)
                print('Connected successfully!')
            except Exception as e:
                self._setActive(False)
                print('Connection failed. Error: ' + str(e))

            time.sleep(CHECK_CONNECTION_SLEEP)

    def isActive(self):
        self._lock.acquire()
        isActiveFlag = self._isActive
        self._lock.release()
        return isActiveFlag

    def execCommandOnServer(self, command):
        message = "Сейчас на остановке 3 человека"
        return message

        self._lock.acquire()
        try:
            ssh_stdin, ssh_stdout, ssh_stderr = self._ssh.exec_command(command)
            message = ssh_stdout.read().decode("utf-8", "ignore")
            ssh_stdin.flush()
        except Exception as e:
            message = 'Нет подключения к майнеру. Ошибка: ' + str(e)
        self._lock.release()

        return message

    def _setActive(self, isActiveFlag):
        self._lock.acquire()
        self._isActive = isActiveFlag
        self._lock.release()
