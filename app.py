from flask import Flask, render_template, request
from flask_socketio import SocketIO
import serial
import mysql.connector
from threading import Lock
from datetime import datetime


mydb = mysql.connector.connect(
  host="localhost",
  user="user_name",
  password="password database",
  database="name database u use"
)


"""
Background Thread
"""
thread = None
thread_lock = Lock()
ser1 = serial.Serial('COM5', 115200)
ser2 = serial.Serial('',115200) 
app = Flask(__name__)
app.config['SECRET_KEY'] = 'donsky!'
socketio = SocketIO(app, cors_allowed_origins='*')

def send_rfid_cmd(cmd):
    data = bytes.fromhex(cmd)
    test_serial.write(data)
    response = test_serial.read(1000)
    response_hex = response.hex().upper()
    hex_list = [response_hex[i:i+2] for i in range(0, len(response_hex), 2)]
    hex_space = ' '.join(hex_list)
    
    if hex_space == 'BB 01 FF 00 01 15 16 7E':
        return "no respon"
    elif hex_space.startswith('BB 02 22 00'):
        return hex_space.split()[-6:-2]  # Ambil ID saja
    else: 
        return None

"""
Get current date time
"""
def get_current_datetime():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def insert_data(flt, date):
    mycursor = mydb.cursor()
    sql = "INSERT INTO sensors_data (value, date) VALUES (%s, %s)"
    val = (flt, date)
    mycursor.execute(sql, val)
    mydb.commit()

"""
Generate random sequence of dummy sensor values and send it to our clients
"""
def background_thread():
    print("Generating Data sensor values")
    while True:
        try:
            data = ser.readline().decode("utf-8")
            print("Raw data:", data)  # Add this line for debugging
            flt = float(data)
            current_datetime = get_current_datetime()
            
            # Insert data into MySQL database
            insert_data(flt, current_datetime)
            
            # Emit data to clients
            socketio.emit('updateSensorData', {'value': flt, "date": current_datetime})
            
            socketio.sleep(5)
        except Exception as e:
            print("Error reading from serial:", e)

"""
Serve root index file
"""
@app.route('/')
def index():
    return render_template('index.html')

"""
Decorator for connect
"""
@socketio.on('connect')
def connect():
    global thread
    print('Client connected')

    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

"""
Decorator for disconnect
"""
@socketio.on('disconnect')
def disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    try:
        socketio.run(app, port=5001)
    finally:
        ser.close()  # Pastikan untuk menutup port serial setelah selesai digunakan
