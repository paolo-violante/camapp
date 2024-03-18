import socket
from cv2 import flip
from kivy.clock import Clock
from functools import partial
from threading import Thread
from kivy.clock import mainthread
import threading
from kivy.app import App
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.animation import Animation
from kivymd.uix.list import OneLineListItem
from kivy.uix.popup import Popup
import logging
import os
import sys
import requests
#from flask import request
import numpy as np
import cv2

import time
import kivy
import datetime
from datetime import timezone
from kivy.utils import platform
if platform == 'android':
    from plyer import vibrator, notification

import pickle
import struct

Builder.load_file('receiver.kv')


class Root(FloatLayout):
    def __init__(self, *args, **kwargs):
        super(Root, self).__init__(*args, **kwargs)

        output_text = ObjectProperty(None)
        livefeed = ObjectProperty(None)
        server_ip = ObjectProperty(None)
        server_port = ObjectProperty(None)
        scrollview = ObjectProperty(None)
        navmap = ObjectProperty(None)
        sidebar = ObjectProperty(None)
        topbar = ObjectProperty(None)
        connect_button = ObjectProperty(None)
        username = ObjectProperty(None)
        password = ObjectProperty(None)

        self.user = ""
        self.pwd = ""
        #self.url = 'http://127.0.0.1:5000/getframe'
        self.url = 'http://192.168.1.66:5000/getframe'
        
        t = Thread(target=self.start_listen_status_thread, args=[self])
        t.daemon = True
        t.start()
        
        
    def start_listen_thread(self, instance):
        

        while True:
            try:
                #Clock.schedule_once(partial(self.output_to_textinput, "1"), 0.1)
                x = requests.get(self.url, params={"username": self.user, "password": self.pwd})
                #Clock.schedule_once(partial(self.output_to_textinput, "2"), 0.1)
                frame = pickle.loads(x.content)
                Clock.schedule_once(partial(self.update_frame, frame), 0.1)
                
            except Exception as e:
                Clock.schedule_once(partial(self.output_to_textinput, "req: "+str(e)+"\n"), 0.1)
        
        
    @mainthread
    def update_frame(self, frame, *args):
        try:
            buffer = flip(frame, 0)
            texture = Texture.create(size=(buffer.shape[1], buffer.shape[0]), colorfmt='rgb')
            buffer = buffer.tobytes()
            texture.blit_buffer(buffer, bufferfmt="ubyte", colorfmt="rgb")
            self.livefeed.texture = texture
        except Exception as e:
            Clock.schedule_once(partial(self.output_to_textinput, "upd: "+str(e)+"\n"), 0.1)


    
    def output_to_textinput(self, data_string, *args):
        maxlines = 25
        temp = self.output_text.text + data_string
        textlist = temp.splitlines()
        if len(textlist) > maxlines:
            newtext = "\n".join(textlist[-maxlines:])
            self.output_text.text = newtext + "\n"
        else:
            self.output_text.text += data_string
        #self.output_text.text += "\n\n"
            
            
            
    def anim_menu(self, *args):
        if self.sidebar.pos_hint["x"] < 0:
            disp = 0
        else:
            disp = -1
        anim = Animation(pos_hint={"x":disp},duration=0.2)
        anim.start(self.sidebar)

        
    def connect(self):
        try:
            self.user = self.username.text
            self.pwd = self.password.text
            self.url = "http://"+self.server_ip+":"+self.server_port+"/getframe"
            #login_url = "http://"+self.server_ip+":"+self.server_port+"/login.html"
            #x = requests.post(self.url, params={self.user: self.pwd})
        except Exception as e:
            Clock.schedule_once(partial(self.output_to_textinput, "conn: "+str(e)+"\n"), 0.1)

        t = Thread(target=self.start_listen_thread, args=[self])
        t.daemon = True
        t.start()
        
        
    def start_listen_status_thread(self, instance):
        
        while True:
            x = requests.get('http://192.168.1.66:5000/getstatus', params={"username": self.user})
            
            status = int(x.content)
            #print(status)
            if(platform == 'android' and status == 1):
                try:
                    Clock.schedule_once(partial(self.output_to_textinput, str(status)), 0.1)
                    notification.notify(title='Camapp', message="attività sospetta rilevata!")
                    vibrator.vibrate(1)
                    time.sleep(20)
                except Exception as e:
                    Clock.schedule_once(partial(self.output_to_textinput, "upd: "+str(e)+"\n"), 0.1)



class Camapp(MDApp): 
    
    def build(self):
        #self.theme_cls.primary_palette = "White"
        self.runningapp = Root()
        return self.runningapp
    


Factory.register('Root', cls=Root)

if __name__ == '__main__':
    Camapp().run()
    Window.close()


'''import socket
from cv2 import flip
from kivy.clock import Clock
from functools import partial
from threading import Thread
from kivy.clock import mainthread
import threading
from kivy.app import App
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.animation import Animation
from kivymd.uix.list import OneLineListItem
from kivy.uix.popup import Popup
import logging
import os
import sys

import time
import kivy
import datetime
from datetime import timezone

import pickle
import struct

Builder.load_file('receiver.kv')


class Root(FloatLayout):
    def __init__(self, *args, **kwargs):
        super(Root, self).__init__(*args, **kwargs)

        output_text = ObjectProperty(None)
        livefeed = ObjectProperty(None)
        
       # Clock.schedule_interval(self.update_livefeed, 1)
        
        t = Thread(target=self.start_listen_thread, args=[self])
        t.daemon = True
        t.start()
        
        
        
    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf

    
    def start_listen_thread(self, instance):
        
        TCP_IP = 'localhost'
        TCP_PORT = 5001

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((TCP_IP, TCP_PORT))
            s.listen(True)
            conn, addr = s.accept()
        
            data = b'' ### CHANGED
            payload_size = struct.calcsize("L") ### CHANGED
        

            while True:

                # Retrieve message size
                while len(data) < payload_size:
                    data += conn.recv(4096)

                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("L", packed_msg_size)[0] ### CHANGED

                # Retrieve all data based on message size
                while len(data) < msg_size:
                    data += conn.recv(4096)

                frame_data = data[:msg_size]
                data = data[msg_size:]

                # Extract frame
                frame = pickle.loads(frame_data)

                Clock.schedule_once(partial(self.update_frame, frame, 0.1))
                # Display
                #cv2.imshow('frame', frame)
                #cv2.waitKey(1)
        except Exception as e:
            Clock.schedule_once(partial(self.output_to_textinput, str(e)+"\n"), 0.1)
        
        
    @mainthread
    def update_frame(self, frame, *args):
        buffer = flip(frame, 0).tobuffer()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buffer, bufferfmt="ubyte", colorfmt="bgr")
        self.livefeed.texture = texture


    def output_to_textinput(self, data_string, *args):
        maxlines = 25
        temp = self.output_text.text + data_string
        textlist = temp.splitlines()
        if len(textlist) > maxlines:
            newtext = "\n".join(textlist[-maxlines:])
            self.output_text.text = newtext + "\n"
        else:
            self.output_text.text += data_string
        #self.output_text.text += "\n\n"



class Camapp(MDApp): 
    
    # Function that returns   self.clocktext.text = str(datetime.datetime.now(timezone.utc))
    # the root widget
    def build(self):
        #self.theme_cls.primary_palette = "White"
        self.runningapp = Root()
        return self.runningapp
    


Factory.register('Root', cls=Root)

# Here our class is initialized 
# and its run() method is called. 
# This initializes and starts 
# our Kivy application.
if __name__ == '__main__':
    Camapp().run()
    Window.close()


'''

