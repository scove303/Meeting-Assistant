import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server")
    sio.emit('text_message', {'text': 'hello'})

@sio.on('start_response')
def on_start(data):
    print("START RESPONSE:", data)

@sio.on('stream_chunk')
def on_chunk(data):
    print("CHUNK:", data)

@sio.on('finish_response')
def on_finish(data):
    print("FINISH:", data['html'][:50] if 'html' in data else data)
    sio.disconnect()

sio.connect('http://localhost:5001')
sio.wait()
