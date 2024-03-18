from flask import Flask, render_template, redirect
import requests
from flask import request
import cv2
import pickle
import numpy as np
import os
import pymongo

myclient = pymongo.MongoClient('mongodb://localhost:27017/')

#dblist = myclient.list_database_names()
#if "camdatabase" not in dblist:
app_db = myclient.camdatabase
db_col = app_db["users"]


app = Flask(__name__, template_folder='template')
data = dict()
status = dict()
frames_received = 0
frame_avg = 0
old_frame_avg = 0

if os.path.isfile("avg.txt"):
    os.remove("avg.txt")
 

#@routes
@app.route('/')
def hello_world():
    return render_template('login.html')



@app.route('/reg', methods=['POST'])
def reg_to_db():
    global db_col
    #print(request.form['username'])
    usr = request.values.get('username')
    psw = request.values.get('password')
    psw2 = request.values.get('password2')
    
    query = { "username": usr }
    mydoc = db_col.find(query)
    if len(list(mydoc))==0 and psw==psw2:
        mydict = { "username": usr, "password": psw }
        x = db_col.insert_one(mydict)
        return render_template('cam.html')
    else:
        return render_template('reg-alert.html')
    
    
    return str(200)


@app.route('/cam', methods=['GET'])
def cam():
    return render_template('cam.html')


@app.route('/getframe', methods=['GET'])
def getfr():
    global data
    global db_col
    #print(request.values.get('password'))
    usr = request.args.get('username')
    psw = request.args.get('password')
    print("usr= ",usr)
    print("psw= ",psw)
    query = { "username": usr }

    mydoc = db_col.find_one(query)
    if mydoc['password'] == psw:
        frame = pickle.dumps(data[usr])
        return frame
    else:
        return str(500)
    

@app.route('/register.html', methods=['GET'])
def get_register():
    return render_template('register.html')


@app.route('/login.html', methods=['GET','POST'])
def get_login():
    if request.method == 'POST':
        global db_col
        #print(request.values.get('password'))
        usr = request.values.get('username')
        psw = request.values.get('password')
        query = { "username": usr }
        print(query)

        mydoc = db_col.find_one(query)
        if mydoc is not None:
            if mydoc['password'] == psw:
                return redirect('cam')
            else:
                return render_template('login-alert.html')
        else:
            return render_template('login-alert.html')
    else:
        return render_template('login.html')


@app.route('/storeframe', methods=['POST'])
def storefr():
    global data
    global frames_received
    global frame_avg
    global old_frame_avg
    #frames_received += 1
    
    
    usr = request.form.get('usr')
    print("usr= ",usr)
    pwd = request.form.get('pwd')
    print("pwd= ",pwd)
    
    dat = request.files.get('snap').read()
    old_data = dat
    
    
    file_bytes = np.fromstring(dat, np.uint8)
    old_file_bytes = np.fromstring(old_data, np.uint8)
    frame_avg = (frame_avg+sum(file_bytes))/2
    print("avg= ", frame_avg)
    f = open("avg.txt","a")
    f.write(str(frame_avg)+"\n")
    if abs(old_frame_avg-frame_avg) > 100000:
        f.write("DETECT\n")
        status[usr] = 1
    else:
        status[usr] = 0
    # convert numpy array to image
    img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
    #cv2.imwrite("please.png", img)
    #data[usr] = img
    data.update({usr: img})
    
    old_frame_avg = frame_avg
    return str(200)


@app.route('/getstatus', methods=['get'])
def getstatus():
    global status
    usr = request.args.get("username")
    print(usr)
    if usr in status:
        return str(status[usr])
    else:
        return str(404)
    
 

if __name__ == '__main__':
    app.run(threaded=True)
    