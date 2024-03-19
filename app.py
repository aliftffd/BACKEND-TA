from flask import Flask, render_template, request
from flask_socketio import SocketIO
import serial
from threading import Lock
from datetime import datetime

"""
Background Thread
"""
thread = None
thread_lock = Lock()
ser = serial.Serial('COM5', 115200)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'donsky!'
socketio = SocketIO(app, cors_allowed_origins='*')

"""
Get current date time
"""
def get_current_datetime():
    now = datetime.now()
    return now.strftime("%m/%d/%Y %H:%M:%S")

"""
Generate random sequence of dummy sensor values and send it to our clients
"""
def background_thread():
    print("Generating Data sensor values")
    while True:
        try:
            data = ser.readline().decode("utf-8")
            flt = float(data)
            socketio.emit('updateSensorData', {'value': flt, "date": get_current_datetime()})
            socketio.sleep(1)
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
