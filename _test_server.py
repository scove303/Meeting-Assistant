import os
import sys
import time
import threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# Extract MOBILE_HTML from audio_assistant_3.py
with open("audio_assistant_3.py", "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find("MOBILE_HTML = \"\"\"") + len("MOBILE_HTML = \"\"\"")
end_idx = content.find("\"\"\"", start_idx)
MOBILE_HTML = content[start_idx:end_idx]

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def index():
    return render_template_string(MOBILE_HTML)

@socketio.on('connect')
def test_connect():
    print("Client connected")
    def send_test():
        time.sleep(1)
        socketio.emit('start_response', {'msg_id': 123})
        time.sleep(0.5)
        socketio.emit('stream_chunk', {'text': 'Hello '})
        time.sleep(0.5)
        socketio.emit('stream_chunk', {'text': 'World!'})
        time.sleep(0.5)
        socketio.emit('finish_response', {'html': '<b>Hello World!</b>'})
        print("Sent all events")
    threading.Thread(target=send_test).start()

if __name__ == '__main__':
    socketio.run(app, host='localhost', port=5002, allow_unsafe_werkzeug=True)
