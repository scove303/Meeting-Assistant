import os
import sys
import pyaudio
import wave
import io
import socket
import logging
import numpy as np
import ctypes
from ctypes import windll
from pynput import keyboard
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread, Event
from groq import Groq
import re
import json
import pyautogui
from PIL import Image, ImageGrab
import requests
import time
import mouse  # Thêm thư viện mouse cho screenshot

# --- THƯ VIỆN WEB SERVER ---
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit

# Tắt log rác Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ===================== CẤU HÌNH =====================
# API Keys
GROQ_API_KEY = "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" 
GEMINI_API_KEY = 'AIzaSyBG8PO_PjKFQc2oQI2GOiVGp5STu3bzAAs' 
GEMINI_MODEL = 'gemini-flash-lite-latest' 

MOBILE_PORT = 5001

# Screenshot Config
SCREENSHOT_HOTKEY = 'z'  # Sẽ kết hợp với Ctrl+Shift+Alt
SCREENSHOT_SAVE_PATH = "screenshots"
SCREENSHOT_QUALITY = 100

if not os.path.exists(SCREENSHOT_SAVE_PATH):
    os.makedirs(SCREENSHOT_SAVE_PATH)

# PLACEHOLDER SYSTEM PROMPT
SYSTEM_PROMPT = r"""
Bạn là một trợ lý Toán học và Khoa học chuyên nghiệp, chuyên về Đại số tuyến tính và các kiến thức cơ bản.

MỤC TIÊU: Giải quyết bài toán một cách trực quan, ngắn gọn, dễ hiểu và tuân thủ nghiêm ngặt định dạng hiển thị.

QUY TẮC HIỂN THỊ (BẮT BUỘC):
1. Ngôn ngữ: 100% Tiếng Việt.
2. Công thức: Dùng LaTeX. Inline là $...$, Block (xuống dòng) là $$...$$.
3. Phong cách: Đi thẳng vào vấn đề. KHÔNG chào hỏi, KHÔNG mở bài/kết bài lan man. KHÔNG giải thích dông dài văn tự.
4. Cấu trúc bài giải: Chia thành các bước rõ ràng. Mỗi bước phải tuân theo format sau:
   ### Bước [n]: [Tên hành động cụ thể]
   - Giải thích: [Lý do ngắn gọn - chỉ 1 câu, nếu cần thiết]
   - Thực hiện: [Trình bày phép tính/biến đổi]
5. Kết quả: Bắt buộc ghi dòng cuối cùng là: **Kết quả: [Đáp án]**

QUY TẮC SƯ PHẠM (Dựa trên chuẩn đầu ra):
1. Phạm vi kiến thức: Tập trung vào Đại số tuyến tính (Vector, Ma trận, Khử Gauss, Không gian vector, Trị riêng/Vector riêng).
2. Phương pháp giải: 
   - Với bài toán khó, hãy chia nhỏ thành các bước sơ cấp nhất.
   - Ưu tiên sử dụng các phương pháp cơ bản (như khử Gauss, định nghĩa gốc) thay vì các định lý phức tạp hoặc đường tắt trừ khi được yêu cầu.
   - Đảm bảo người mới học (level beginner) có thể hiểu được logic biến đổi.

VÍ DỤ MẪU VỀ CÁCH TRÌNH BÀY:
User: Giải hệ phương trình: x + y = 3, 2x - y = 0
AI:
### Bước 1: Viết ma trận bổ sung
- Biểu diễn hệ dưới dạng $[A|b]$:
$$ \left[\begin{array}{cc|c} 1 & 1 & 3 \\ 2 & -1 & 0 \end{array}\right] $$

### Bước 2: Khử Gauss (Khử phần tử ở dòng 2, cột 1)
- Lấy dòng 2 trừ đi 2 lần dòng 1 ($R_2 \leftarrow R_2 - 2R_1$):
$$ \left[\begin{array}{cc|c} 1 & 1 & 3 \\ 0 & -3 & -6 \end{array}\right] $$

### Bước 3: Tìm nghiệm từ dưới lên
- Từ dòng 2: $-3y = -6 \Rightarrow y = 2$.
- Thay vào dòng 1: $x + 2 = 3 \Rightarrow x = 1$.

**Kết quả: $x = 1, y = 2$**


các chuẩn kiến thức, kỹ năng đầu ra như sau:

1. Hiểu được vector

- Hiểu được các phép toán cơ bản của vector cộng, trừ,  vector nhân vector với một số thực

2. Hiểu được các phép nâng cao như:

- Tổ hợp tuyến tính của vector, nhân trong (tích vô hướng), độ dài vector ánh xạ tuyến tính của vector"

3. Hiểu được ánh xạ tuyến tính

- Hiểu được nguyên lý quy nạp

- Hiểu được anh xạ tuyến tính được biểu diễn dưới dạng ma trận"

4. Nắm dược các khái niệm cơ bản của ma trận như:

- Ma trận 0, 

- Ma trận đơn vị, 

- Ma trận chéo, 

- Ma trận tam giác, 

- Ma trận chuyển vị, 

- Ma trận đối xứng

5. Hiểu được các phép toán của ma trận như:

- Nhân ma trận với một số

- Cộng hai ma trận cùng cỡ

6. Nắm được điều kiện để nhân ma trận với một vector, Hiểu được các nhân giữa ma trận và vector (dot product)"

7. Nắm được cách nhân ma trận chuyển vị với một vector, một ma trận tam giác với một vector, ma trận đối xứng với một vector

8. Nắm được từ ánh xạ tuyến tính đến nhân ma trận với ma trận

9. Hiểu được điều kiện và thực hiện phép nhân hai ma trận

10. Hiểu được cách phân chia một ma trận thành nhiều ma trận con để thực hiện phép nhân

11. Hiểu dược khử Gauss, thêm ma trận vào bên phải, biến đổi Gauss đồng thời cả hai ma trận

12. Hiểu được cách giải phương trình ma trận Ax = b bằng khử Gauss (đưa ma trận về dạng tam giác trên và tam giác dưới)

13. Hiểu khử Gauss để tìm ma trận nghịch đảo

14. Hiểu được giải phương trình Ax = b bằng cách tìm ma trận nghịch đảo

15. Nắm được các khái niệm về không gian vector như:

- Không gian con, không gian cột, không gian Null"

16. Hiểu được span, độc lập tuyến tính, cơ sở của không gian con, số chiều của không gian con

17. Hiểu thêm về không gian vector như: 

- Vector trực giao và không gian trực giao

- Hiểu được lời giải gần đúng bằng phương pháp bình phương tối thiểu"

18. Nắm được phép chiếu vector xuống một không gian con, cơ sở trực chuẩn, chuyển đổi cơ sở

19. Nắm được khái niệm về trị riêng, vector riêng và các bài toán liên quan
"""

# Audio Config
CHUNK = 8192
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
MAX_HISTORY = 10 # Tăng lịch sử chat lên để nhớ lâu hơn

# ===================== GIAO DIỆN ĐIỆN THOẠI (HTML - FIX RENDER) =====================
MOBILE_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Audio Controller</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', Roboto, sans-serif; padding: 10px; line-height: 1.6; }
        #status { font-size: 12px; color: #569cd6; margin-bottom: 10px; text-align: center; border-bottom: 1px solid #333; padding-bottom: 10px;}
        
        .msg { padding: 12px 16px; border-radius: 8px; margin-bottom: 15px; word-wrap: break-word; }
        .user { background: #264f78; text-align: right; margin-left: 15%; color: #fff; }
        .ai { background: #1e1e1e; border-left: 4px solid #569cd6; margin-right: 5%; }
        
        pre { background: #2d2d2d; padding: 10px; overflow-x: auto; border-radius: 6px; border: 1px solid #444; }
        code { font-family: 'Consolas', monospace; color: #9cdcfe; }
        
        /* MathJax Overflow Fix */
        mjx-container { overflow-x: auto; overflow-y: hidden; max-width: 100%; padding: 5px 0; }
        .math-block { margin: 10px 0; text-align: center; }

        /* Input area */
        #input-container { position: fixed; bottom: 0; width: 100%; left: 0; padding: 10px; background: #121212; display: flex; border-top: 1px solid #333; }
        input { flex-grow: 1; padding: 12px; border-radius: 20px; border: 1px solid #333; background: #222; color: white; margin-right: 10px; outline: none; }
        button { padding: 10px 20px; border-radius: 20px; border: none; background: #007acc; color: white; font-weight: bold; }
    </style>
    
    <script>
    MathJax = {
        tex: {
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
            processEscapes: true
        },
        svg: { fontCache: 'global' }
    };
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <div id="status">● System Controller (Connected)</div>
    <div id="container" style="padding-bottom: 80px;"></div>
    <div id="input-container">
        <input id="text-input" placeholder="Type command..." autocomplete="off"/>
        <button onclick="send()">Send</button>
    </div>
    <script>
        var socket = io();
        var container = document.getElementById('container');
        var currentDiv = null;

        socket.on('new_user_message', function(data) { addMessage('user', data.content); });

        socket.on('start_response', function() {
            currentDiv = document.createElement('div');
            currentDiv.className = 'msg ai';
            container.appendChild(currentDiv);
            window.scrollTo(0, document.body.scrollHeight);
        });

        socket.on('stream_chunk', function(data) {
            if (!currentDiv) return;
            // Chỉ hiển thị text thô khi đang stream để tránh vỡ HTML
            let display = data.text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            currentDiv.innerHTML += display.replace(/\\n/g, "<br>");
            window.scrollTo(0, document.body.scrollHeight);
        });

        socket.on('finish_response', function(data) {
            if (!currentDiv) return;
            // Khi xong mới render HTML + MathJax
            currentDiv.innerHTML = data.html; 
            MathJax.typesetPromise([currentDiv]).then(() => {
                window.scrollTo(0, document.body.scrollHeight);
            });
            currentDiv = null;
        });
        
        socket.on('clear_chat', function() { container.innerHTML = '<div class="msg ai">🧹 Memory Cleared.</div>'; });

        function send() {
            var val = document.getElementById('text-input').value;
            if(val) { socket.emit('text_message', {text: val}); addMessage('user', val); document.getElementById('text-input').value = ''; }
        }
        
        function addMessage(role, text) {
            var div = document.createElement('div');
            div.className = 'msg ' + role;
            div.innerHTML = text.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\\n/g, '<br>');
            container.appendChild(div);
            window.scrollTo(0, document.body.scrollHeight);
        }
    </script>
</body>
</html>
"""

class AudioMobileServer:
    def __init__(self, assistant_ref):
        self.assistant = assistant_ref
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        @self.app.route('/')
        def index():
            return render_template_string(MOBILE_HTML)
        
        @self.socketio.on('text_message')
        def handle_text_message(data):
            text = data.get('text', '').strip()
            if text:
                Thread(target=self.assistant.process_text_input, args=(text,), daemon=True).start()
        
    def run(self):
        self.socketio.run(self.app, host='0.0.0.0', port=MOBILE_PORT, allow_unsafe_werkzeug=True)

    def send_user_message(self, content):
        self.socketio.emit('new_user_message', {'content': content})

    def emit_start(self):
        self.socketio.emit('start_response')

    def emit_chunk(self, text):
        self.socketio.emit('stream_chunk', {'text': text})

    def emit_finish(self, html):
        self.socketio.emit('finish_response', {'html': html})

    def clear(self):
        self.socketio.emit('clear_chat')

class SystemAudioControl:
    def __init__(self):
        self.client = None
        self.setup_groq()
        
        self.root = None
        self.is_recording = False
        self.is_processing_image = False
        self.is_screenshot_mode = False  # Flag cho screenshot mode
        self.screenshot_start_pos = None  # Vị trí bắt đầu screenshot
        self.stop_event = Event()
        self.audio = pyaudio.PyAudio()
        
        self.system_frames = []
        self.mic_frames = []
        self.conversation_history = []
        
        # === VARIABLES CHO CẤU HÌNH ẢNH ===
        self.scan_w_var = None
        self.scan_h_var = None
        
        # === WEB SERVER MOBILE ===
        self.server = AudioMobileServer(self)

    def setup_groq(self):
        try:
            self.client = Groq(api_key=GROQ_API_KEY)
        except Exception as e:
            print(f"Groq Init Error: {e}")

    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("🎙 System Audio Controller")
        self.root.geometry("960x750")
        self.root.configure(bg='#1e1e1e')
        
        # Xử lý khi đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # === TOP FRAME - STATUS & DEVICE INFO ===
        top_frame = tk.Frame(self.root, bg='#1e1e1e', pady=5)
        top_frame.pack(fill=tk.X, padx=10)

        # Status Label
        self.status_lbl = tk.Label(top_frame, text="● Idle", font=('Consolas', 10, 'bold'), 
                                  fg='#569cd6', bg='#1e1e1e', anchor='w')
        self.status_lbl.pack(side=tk.LEFT, padx=(0,10))

        # Device Label
        self.device_lbl = tk.Label(top_frame, text="Checking Devices...", font=('Consolas', 8), 
                                  fg='#999', bg='#1e1e1e', anchor='w')
        self.device_lbl.pack(side=tk.LEFT)

        # === CONTROL PANEL FRAME - SLIDERS & TOGGLES ===
        control_panel = tk.Frame(self.root, bg='#252526', relief='flat', bd=1)
        control_panel.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Row 1: Scan Size Sliders
        slider_row1 = tk.Frame(control_panel, bg='#252526', pady=5)
        slider_row1.pack(fill=tk.X, padx=10)

        # Scan Width Slider
        tk.Label(slider_row1, text="Scan Width:", fg='#dcdcaa', bg='#252526', 
                font=('Consolas', 9)).pack(side=tk.LEFT, padx=(0,5))
        self.scan_w_var = tk.IntVar(value=500)
        self.scan_w_label = tk.Label(slider_row1, text="500px", fg='#4ec9b0', bg='#252526', 
                                     font=('Consolas', 9, 'bold'), width=6)
        self.scan_w_label.pack(side=tk.LEFT, padx=(0,5))
        scan_w_slider = tk.Scale(slider_row1, from_=100, to=2000, orient=tk.HORIZONTAL,
                                variable=self.scan_w_var, bg='#252526', fg='#d4d4d4',
                                activebackground='#569cd6', highlightthickness=0,
                                troughcolor='#3c3c3c', length=150, width=15,
                                command=lambda v: self.scan_w_label.config(text=f"{v}px"))
        scan_w_slider.pack(side=tk.LEFT, padx=(0,20))

        # Scan Height Slider
        tk.Label(slider_row1, text="Scan Height:", fg='#dcdcaa', bg='#252526',
                font=('Consolas', 9)).pack(side=tk.LEFT, padx=(0,5))
        self.scan_h_var = tk.IntVar(value=500)
        self.scan_h_label = tk.Label(slider_row1, text="500px", fg='#4ec9b0', bg='#252526',
                                     font=('Consolas', 9, 'bold'), width=6)
        self.scan_h_label.pack(side=tk.LEFT, padx=(0,5))
        scan_h_slider = tk.Scale(slider_row1, from_=100, to=2000, orient=tk.HORIZONTAL,
                                variable=self.scan_h_var, bg='#252526', fg='#d4d4d4',
                                activebackground='#569cd6', highlightthickness=0,
                                troughcolor='#3c3c3c', length=150, width=15,
                                command=lambda v: self.scan_h_label.config(text=f"{v}px"))
        scan_h_slider.pack(side=tk.LEFT)

        # Row 2: Screenshot Quality & Debug Mode
        slider_row2 = tk.Frame(control_panel, bg='#252526', pady=5)
        slider_row2.pack(fill=tk.X, padx=10)

        # Screenshot Quality Slider
        tk.Label(slider_row2, text="Screenshot Quality:", fg='#dcdcaa', bg='#252526',
                font=('Consolas', 9)).pack(side=tk.LEFT, padx=(0,5))
        self.screenshot_quality_var = tk.IntVar(value=95)
        self.quality_label = tk.Label(slider_row2, text="95%", fg='#4ec9b0', bg='#252526',
                                      font=('Consolas', 9, 'bold'), width=5)
        self.quality_label.pack(side=tk.LEFT, padx=(0,5))
        quality_slider = tk.Scale(slider_row2, from_=50, to=100, orient=tk.HORIZONTAL,
                                 variable=self.screenshot_quality_var, bg='#252526', fg='#d4d4d4',
                                 activebackground='#569cd6', highlightthickness=0,
                                 troughcolor='#3c3c3c', length=120, width=15,
                                 command=lambda v: self.quality_label.config(text=f"{v}%"))
        quality_slider.pack(side=tk.LEFT, padx=(0,20))

        # Debug Mode Toggle
        tk.Label(slider_row2, text="Debug Mode:", fg='#dcdcaa', bg='#252526',
                font=('Consolas', 9)).pack(side=tk.LEFT, padx=(0,5))
        self.debug_mode_var = tk.BooleanVar(value=False)
        self.debug_status = tk.Label(slider_row2, text="OFF", fg='#ff4444', bg='#252526',
                                     font=('Consolas', 9, 'bold'), width=5)
        self.debug_status.pack(side=tk.LEFT, padx=(0,5))
        debug_toggle = tk.Checkbutton(slider_row2, variable=self.debug_mode_var,
                                     bg='#252526', activebackground='#252526',
                                     selectcolor='#3c3c3c', fg='#4ec9b0',
                                     command=self.toggle_debug_mode)
        debug_toggle.pack(side=tk.LEFT, padx=(0,20))

        # Auto-save Screenshots Toggle
        tk.Label(slider_row2, text="Auto-save:", fg='#dcdcaa', bg='#252526',
                font=('Consolas', 9)).pack(side=tk.LEFT, padx=(0,5))
        self.auto_save_var = tk.BooleanVar(value=True)
        self.autosave_status = tk.Label(slider_row2, text="ON", fg='#4ec9b0', bg='#252526',
                                        font=('Consolas', 9, 'bold'), width=5)
        self.autosave_status.pack(side=tk.LEFT, padx=(0,5))
        autosave_toggle = tk.Checkbutton(slider_row2, variable=self.auto_save_var,
                                        bg='#252526', activebackground='#252526',
                                        selectcolor='#3c3c3c', fg='#4ec9b0',
                                        command=self.toggle_autosave)
        autosave_toggle.pack(side=tk.LEFT)

        # === TEXT AREA ===
        text_frame = tk.Frame(self.root, bg='#1e1e1e')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,5))

        self.text_area = scrolledtext.ScrolledText(
            text_frame, wrap=tk.WORD, state='disabled',
            bg='#1e1e1e', fg='#d4d4d4', insertbackground='white',
            font=('Consolas', 10), relief='flat', borderwidth=0
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # === DEFINE TAGS ===
        self.text_area.tag_config('user_tag', foreground='#4ec9b0', font=('Consolas', 10, 'bold'))
        self.text_area.tag_config('ai_tag', foreground='#569cd6', font=('Consolas', 10, 'bold'))
        self.text_area.tag_config('separator', foreground='#3c3c3c')
        self.text_area.tag_config('header', foreground='#dcdcaa', font=('Consolas', 11, 'bold'))
        self.text_area.tag_config('code', background='#2d2d30', foreground='#9cdcfe', font=('Consolas', 9))
        self.text_area.tag_config('bold', font=('Consolas', 10, 'bold'), foreground='#d7ba7d')
        self.text_area.tag_config('normal_text', foreground='#d4d4d4')
        
        # === INPUT FRAME - TEXT INPUT & SEND BUTTON ===
        input_frame = tk.Frame(self.root, bg='#252526', pady=8)
        input_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        # Text input
        tk.Label(input_frame, text="💬", font=('Segoe UI Emoji', 12), 
                bg='#252526', fg='#569cd6').pack(side=tk.LEFT, padx=(5, 5))
        
        self.text_input = tk.Entry(input_frame, font=('Consolas', 10), 
                                   bg='#1e1e1e', fg='#d4d4d4', 
                                   insertbackground='white', relief='flat', bd=0)
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=6)
        self.text_input.bind('<Return>', lambda e: self.send_text_message())
        
        # Send button
        send_btn = tk.Button(input_frame, text="Send ➤", font=('Consolas', 9, 'bold'),
                            bg='#569cd6', fg='white', activebackground='#4ec9b0',
                            relief='flat', padx=20, pady=5, cursor='hand2',
                            command=self.send_text_message)
        send_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Clear button
        clear_btn = tk.Button(input_frame, text="Clear", font=('Consolas', 9),
                             bg='#3c3c3c', fg='#d4d4d4', activebackground='#555',
                             relief='flat', padx=15, pady=5, cursor='hand2',
                             command=self.clear_chat)
        clear_btn.pack(side=tk.LEFT)
        
        # === BOTTOM BAR - INFO ===
        bottom_frame = tk.Frame(self.root, bg='#1e1e1e', pady=5)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(5,10))
        
        ip_text = self._get_ip()
        hotkeys = f"[Ctrl+Shift+Alt+R: Record] [Ctrl+Shift+Alt+S: Scan] [Ctrl+Shift+Alt+Z: Screenshot]"
        ip_label = tk.Label(bottom_frame, text=f"Mobile: http://{ip_text}:{MOBILE_PORT}  |  {hotkeys}", 
                          font=('Consolas', 8), fg='#999', bg='#1e1e1e')
        ip_label.pack(side=tk.LEFT)

        # === POST-INIT ===
        self.update_device_info()
        self.root.after(100, lambda: self.status_lbl.config(text="● Ready", fg='#4ec9b0'))

    def _get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"

    def toggle_debug_mode(self):
        """Toggle debug mode on/off"""
        if self.debug_mode_var.get():
            self.debug_status.config(text="ON", fg='#4ec9b0')
            print("🐛 Debug mode enabled")
        else:
            self.debug_status.config(text="OFF", fg='#ff4444')
            print("🐛 Debug mode disabled")

    def toggle_autosave(self):
        """Toggle auto-save screenshots on/off"""
        if self.auto_save_var.get():
            self.autosave_status.config(text="ON", fg='#4ec9b0')
            print("💾 Auto-save enabled")
        else:
            self.autosave_status.config(text="OFF", fg='#ff4444')
            print("💾 Auto-save disabled")

    def send_text_message(self):
        """Gửi tin nhắn từ text input"""
        text = self.text_input.get().strip()
        if not text:
            return
        
        # Clear input
        self.text_input.delete(0, tk.END)
        
        # Display user message
        self.format_and_insert("User", text)
        self.server.send_user_message(text)
        
        # Process
        Thread(target=self.process_text_input, args=(text,), daemon=True).start()

    def clear_chat(self):
        """Xóa toàn bộ chat history"""
        self.conversation_history = []
        self.text_area.configure(state='normal')
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert(tk.END, "🧹 Chat cleared. Memory reset.\n", 'ai_tag')
        self.text_area.configure(state='disabled')
        self.server.clear()
        print("🧹 Chat history cleared")

    # === TRIGGER IMAGE SCAN (GỐC) ===
    def trigger_image_scan(self):
        if self.is_processing_image: return
        self.is_processing_image = True
        self.root.after(0, lambda: self.status_lbl.config(text="📸 Scanning...", fg='#dcdcaa'))
        Thread(target=self._process_image_scan, daemon=True).start()

    # === TRIGGER SCREENSHOT (MỚI) ===
    def trigger_screenshot(self):
        """Bắt đầu chế độ screenshot khi nhấn hotkey"""
        if self.is_processing_image or self.is_screenshot_mode:
            return
        
        self.is_screenshot_mode = True
        self.screenshot_start_pos = mouse.get_position()
        self.root.after(0, lambda: self.status_lbl.config(text="📸 Screenshot Mode - Drag to select area...", fg='#dcdcaa'))
        print(f"🟢 Screenshot started at: {self.screenshot_start_pos}")

    def finish_screenshot(self):
        """Kết thúc screenshot và xử lý ảnh"""
        if not self.is_screenshot_mode:
            return
        
        end_pos = mouse.get_position()
        start_pos = self.screenshot_start_pos
        self.is_screenshot_mode = False
        
        print(f"🔴 Screenshot ended at: {end_pos}")
        
        # Kiểm tra nếu vùng chọn quá nhỏ
        x1, y1 = start_pos
        x2, y2 = end_pos
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        if width < 5 or height < 5:
            print(f"❌ Vùng chọn quá nhỏ ({width}x{height}), không chụp.")
            self.root.after(0, lambda: self.status_lbl.config(text="⚠️ Area too small", fg='#ff4444'))
            self.root.after(2000, lambda: self.status_lbl.config(text="● Ready", fg='#4ec9b0'))
            return
        
        # Chụp ảnh và xử lý
        Thread(target=self._process_screenshot, args=(start_pos, end_pos), daemon=True).start()

    def _process_screenshot(self, start_pos, end_pos):
        """Xử lý screenshot tương tự như scan image"""
        try:
            self.is_processing_image = True
            
            x1, y1 = start_pos
            x2, y2 = end_pos
            
            # Tính toán vùng chọn
            left, top = min(x1, x2), min(y1, y2)
            right, bottom = max(x1, x2), max(y1, y2)
            
            width = right - left
            height = bottom - top

            if self.debug_mode_var.get():
                print(f"📸 Chụp vùng: ({left}, {top}) → ({right}, {bottom}) | {width}x{height}px")

            # Chụp màn hình
            img = ImageGrab.grab(bbox=(left, top, right, bottom))
            
            # Lưu file nếu auto-save bật
            filename = None
            if self.auto_save_var.get():
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(SCREENSHOT_SAVE_PATH, f"snap_{timestamp}.jpg")
                # Sử dụng quality từ slider
                quality = self.screenshot_quality_var.get()
                img.save(filename, "JPEG", quality=quality, optimize=True)
                if self.debug_mode_var.get():
                    print(f"✅ Đã lưu: {filename} (quality: {quality}%)")
            
            # Encode và gửi đến Gemini giống như scan
            self.root.after(0, lambda: self.status_lbl.config(text="🔄 Analyzing Screenshot...", fg='#569cd6'))
            
            import base64
            buffered = io.BytesIO()
            # Sử dụng quality từ slider cho encode
            encode_quality = self.screenshot_quality_var.get()
            img.save(buffered, format="JPEG", quality=encode_quality)
            img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # Gọi Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            
            # --- PHẦN SỬA ĐỔI: TẠO PROMPT THÔNG MINH ---
            # 1. Lấy yêu cầu thực tế của user (nếu có gõ văn bản trước khi bấm phím tắt)
            user_query = "Hãy đọc và giải quyết yêu cầu/câu hỏi có trong ảnh này."
            if self.conversation_history:
                last_msg = self.conversation_history[-1]
                if last_msg['role'] == 'user':
                    user_query = last_msg['content']

            # 2. Tạo Prompt tổng hợp bao gồm SYSTEM_PROMPT để ép AI tuân thủ quy tắc
            final_prompt = (
                f"Dưới đây là các quy tắc và vai trò bạn phải tuân thủ:\n{SYSTEM_PROMPT}\n\n"
                f"YÊU CẦU CỤ THỂ: {user_query}\n\n"
                f"NHIỆM VỤ: Dựa trên hình ảnh screenshot đính kèm, hãy thực hiện yêu cầu trên theo đúng các quy tắc đã nêu."
            )
            # ------------------------------------------

            payload = {
                "contents": [{
                    "parts": [
                        {"text": final_prompt}, # Gửi prompt tổng hợp thay vì prompt cũ
                        {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                    ]
                }]
            }

            if self.debug_mode_var.get():
                print(f"🤖 Đang gửi đến Gemini API...")
            
            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Gemini API Error: {response.status_code} - {response.text}")

            result = response.json()
            answer = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No response')

            if self.debug_mode_var.get():
                print(f"✅ Nhận được phản hồi từ Gemini")

            # Hiển thị kết quả
            self.root.after(0, lambda: self.status_lbl.config(text="✅ Screenshot Analyzed", fg='#4ec9b0'))
            
            # Format và hiển thị như bình thường
            save_info = f" [Saved: {filename}]" if filename else ""
            # Lưu user_query gốc vào lịch sử cho sạch sẽ
            self.conversation_history.append({"role": "user", "content": f"[Screenshot {width}x{height}px]{save_info} {user_query}"})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            if len(self.conversation_history) > MAX_HISTORY * 2:
                self.conversation_history = self.conversation_history[-MAX_HISTORY*2:]

            # Mobile UI
            self.server.send_user_message(f"📸 Screenshot ({width}x{height}px): {user_query}")
            self.server.emit_start()
            
            # Stream to mobile
            for chunk in answer.split():
                self.server.emit_chunk(chunk + " ")
                time.sleep(0.01)
            
            html_answer = self.markdown_to_html(answer)
            self.server.emit_finish(html_answer)

            # PC UI
            self.root.after(0, lambda: self._finalize_pc_display(answer))
            self.root.after(2000, lambda: self.status_lbl.config(text="● Ready", fg='#4ec9b0'))

        except requests.exceptions.Timeout:
            error_msg = "❌ Timeout khi kết nối Gemini API"
            if self.debug_mode_var.get():
                print(error_msg)
            self.root.after(0, lambda: self.status_lbl.config(text="❌ API Timeout", fg='#ff4444'))
            self.server.emit_chunk(f"\n❌ API Timeout - Vui lòng thử lại")
        except Exception as e:
            error_msg = f"❌ Lỗi: {e}"
            if self.debug_mode_var.get():
                print(error_msg)
            self.root.after(0, lambda: self.status_lbl.config(text="❌ Error", fg='#ff4444'))
            self.server.emit_chunk(f"\n❌ Error: {str(e)}")
        finally:
            self.is_processing_image = False
            self.root.after(2000, lambda: self.status_lbl.config(text="● Ready", fg='#4ec9b0'))

    def _process_image_scan(self):
        try:
            # Lấy vị trí chuột
            cx, cy = pyautogui.position()
            scan_w = self.scan_w_var.get()
            scan_h = self.scan_h_var.get()
            
            # Tính toán tọa độ cắt
            left = max(0, cx - scan_w // 2)
            top = max(0, cy - scan_h // 2)
            right = left + scan_w
            bottom = top + scan_h
            
            # Chụp và encode
            img = ImageGrab.grab(bbox=(left, top, right, bottom))
            
            import base64
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=95)
            img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # === CALL GEMINI API ===
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            
            # 1. Xác định câu hỏi của User (giữ nguyên logic lấy tin nhắn cuối)
            user_query = "Hãy đọc và giải quyết yêu cầu/câu hỏi có trong ảnh này."
            if self.conversation_history:
                last_msg = self.conversation_history[-1]
                if last_msg['role'] == 'user':
                    user_query = last_msg['content']

            # 2. Tạo Prompt tổng hợp (Ép Gemini tuân thủ SYSTEM_PROMPT)
            # Dòng này giúp AI hiểu nó là ai và phải làm gì với cái ảnh
            final_prompt = (
                f"Dưới đây là hướng dẫn về vai trò và quy tắc trả lời của bạn:\n{SYSTEM_PROMPT}\n\n"
                f"YÊU CẦU HIỆN TẠI: {user_query}\n\n"
                f"NHIỆM VỤ: Hãy nhìn vào hình ảnh đính kèm, thực hiện yêu cầu trên theo đúng phong cách và quy tắc đã nêu."
            )

            payload = {
                "contents": [{
                    "parts": [
                        {"text": final_prompt}, # Gửi prompt đã bao gồm quy tắc hệ thống
                        {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                    ]
                }]
            }

            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Gemini API Error: {response.status_code} - {response.text}")

            result = response.json()
            answer = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No response')

            # Cập nhật trạng thái
            self.root.after(0, lambda: self.status_lbl.config(text="✅ Scan Complete", fg='#4ec9b0'))
            
            # Lưu vào lịch sử (Lưu user_query gốc để tránh làm rác lịch sử bằng SYSTEM_PROMPT)
            self.conversation_history.append({"role": "user", "content": f"[Image Scan] {user_query}"})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            if len(self.conversation_history) > MAX_HISTORY * 2:
                self.conversation_history = self.conversation_history[-MAX_HISTORY*2:]

            # === MOBILE RESPONSE ===
            self.server.send_user_message(f"📸 Image Scan: {user_query}")
            self.server.emit_start()
            
            # Stream từng từ
            for chunk in answer.split():
                self.server.emit_chunk(chunk + " ")
                time.sleep(0.01)
            
            html_answer = self.markdown_to_html(answer)
            self.server.emit_finish(html_answer)

            # === PC RESPONSE ===
            self.root.after(0, lambda: self._finalize_pc_display(answer))
            self.root.after(2000, lambda: self.status_lbl.config(text="● Ready", fg='#4ec9b0'))

        except Exception as e:
            print(e)
            self.root.after(0, lambda: self.status_lbl.config(text="❌ Error", fg='#ff4444'))
            self.server.emit_chunk(f"\n❌ Error: {str(e)}")
        
        self.is_processing_image = False

    # === TEXT INPUT PROCESSING ===
    def process_text_input(self, user_text):
        """Xử lý input văn bản từ mobile hoặc bất kỳ nguồn nào"""
        try:
            # Thêm vào lịch sử
            self.conversation_history.append({"role": "user", "content": user_text})
            if len(self.conversation_history) > MAX_HISTORY * 2:
                self.conversation_history = self.conversation_history[-MAX_HISTORY*2:]

            # Chuẩn bị messages cho Groq
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(self.conversation_history)

            # Stream Response
            self.root.after(0, lambda: self.status_lbl.config(text="💬 Thinking...", fg='#569cd6'))
            self.server.emit_start()

            full_answer = ""
            stream = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                stream=True
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_answer += delta
                    self.server.emit_chunk(delta)

            # Lưu lại câu trả lời
            self.conversation_history.append({"role": "assistant", "content": full_answer})

            # Finish Mobile
            html_answer = self.markdown_to_html(full_answer)
            self.server.emit_finish(html_answer)

            # Finish PC
            self.root.after(0, lambda: self._finalize_pc_display(full_answer))
            self.root.after(0, lambda: self.status_lbl.config(text="● Ready", fg='#4ec9b0'))

        except Exception as e:
            print(f"Error in text processing: {e}")
            self.root.after(0, lambda: self.status_lbl.config(text="❌ Error", fg='#ff4444'))
            self.server.emit_chunk(f"\n❌ Error: {str(e)}")

    # === MARKDOWN HELPERS ===
    def markdown_to_html(self, text):
        """Convert markdown to HTML cho mobile"""
        html = text
        
        # Code blocks
        html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
        
        # Inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # Bold
        html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)
        
        # Headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Line breaks
        html = html.replace('\n', '<br>')
        
        return html

    def insert_formatted_text_to_pc(self, text):
        """Insert formatted text vào PC text area"""
        lines = text.split('\n')
        for line in lines:
            # Headers
            if line.startswith('###'):
                self.text_area.insert(tk.END, line[3:].strip() + '\n', 'header')
            elif line.startswith('##'):
                self.text_area.insert(tk.END, line[2:].strip() + '\n', 'header')
            elif line.startswith('#'):
                self.text_area.insert(tk.END, line[1:].strip() + '\n', 'header')
            
            # Code blocks
            elif line.strip().startswith('```'):
                continue
            
            # Bold text
            elif '**' in line:
                parts = re.split(r'(\*\*[^*]+\*\*)', line)
                for part in parts:
                    if part.startswith('**') and part.endswith('**'):
                        self.text_area.insert(tk.END, part[2:-2], 'bold')
                    else:
                        self.text_area.insert(tk.END, part, 'normal_text')
                self.text_area.insert(tk.END, '\n')
            
            # Inline code
            elif '`' in line:
                parts = re.split(r'(`[^`]+`)', line)
                for part in parts:
                    if part.startswith('`') and part.endswith('`'):
                        self.text_area.insert(tk.END, part[1:-1], 'code')
                    else:
                        self.text_area.insert(tk.END, part, 'normal_text')
                self.text_area.insert(tk.END, '\n')
            
            # Normal text
            else:
                self.text_area.insert(tk.END, line + '\n', 'normal_text')

    # === CORE HELPERS ===
    def _finalize_pc_display(self, full_answer):
        self.text_area.configure(state='normal')
        try:
            user_ranges = self.text_area.tag_ranges('user_tag')
            if user_ranges:
                user_end = user_ranges[-1]
                self.text_area.delete(user_end, tk.END)
            self.text_area.insert(tk.END, f"\nSystem Response:\n", 'ai_tag')
            self.insert_formatted_text_to_pc(full_answer)
            self.text_area.insert(tk.END, "\n" + "_"*40 + "\n", 'separator')
        except:
            self.text_area.insert(tk.END, full_answer + "\n", 'normal_text')
        self.text_area.configure(state='disabled')
        self.text_area.see(tk.END)
        
    def format_and_insert(self, speaker, text):
        self.text_area.configure(state='normal')
        if speaker == "User":
            self.text_area.insert(tk.END, f"\nUser: {text}\n", 'user_tag')
        else:
            self.text_area.insert(tk.END, f"\nSystem Response:\n", 'ai_tag')
        self.text_area.configure(state='disabled')
        self.text_area.see(tk.END)

    def update_device_info(self):
        try:
            info_text = ""
            for i in range(self.audio.get_device_count()):
                dev = self.audio.get_device_info_by_index(i)
                if dev['maxInputChannels'] > 0 and \
                    any(k in dev['name'].lower() for k in ['cable', 'stereo mix', 'loopback']):
                    info_text += f"In: {dev['name'][:15]}.. | "
                    break
            default_dev = self.audio.get_default_input_device_info()
            info_text += f"Mic: {default_dev['name'][:15]}.."
            self.device_lbl.config(text=info_text)
        except Exception as e:
            self.device_lbl.config(text=f"Driver: {str(e)[:15]}")
        
    # === AUDIO RECORDING LOGIC ===
    def start_recording(self):
        if self.is_recording: return
        self.is_recording = True
        self.system_frames = []
        self.mic_frames = []
        self.stop_event.clear()
        self.root.after(0, lambda: self.status_lbl.config(text="● Recording...", fg='#dcdcaa'))
        Thread(target=self._record_system, daemon=True).start()
        Thread(target=self._record_mic, daemon=True).start()
        
    def _record_system(self):
        dev_idx = None
        target_rate = RATE
        try:
            for i in range(self.audio.get_device_count()):
                dev = self.audio.get_device_info_by_index(i)
                if dev['maxInputChannels'] > 0 and \
                    any(k in dev['name'].lower() for k in ['cable', 'stereo mix']):
                    dev_idx = i
                    target_rate = int(dev['defaultSampleRate'])
                    break
            if dev_idx is None:
                default_dev = self.audio.get_default_input_device_info()
                target_rate = int(default_dev['defaultSampleRate'])
                
            stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=target_rate,
                                   input=True, input_device_index=dev_idx, frames_per_buffer=CHUNK)
            while not self.stop_event.is_set():
                self.system_frames.append(stream.read(CHUNK, exception_on_overflow=False))
            stream.stop_stream()
            stream.close()
        except: pass

    def _record_mic(self):
        try:
            dev = self.audio.get_default_input_device_info()
            rate = int(dev['defaultSampleRate'])
            stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=rate,
                                   input=True, frames_per_buffer=CHUNK)
            while not self.stop_event.is_set():
                self.mic_frames.append(stream.read(CHUNK, exception_on_overflow=False))
            stream.stop_stream()
            stream.close()
        except: pass

    def stop_recording(self):
        if not self.is_recording: return
        self.is_recording = False
        self.stop_event.set()
        self.root.after(0, lambda: self.status_lbl.config(text="● Processing Audio...", fg='#569cd6'))
        Thread(target=self._process_dual, daemon=True).start()

    def _mix_audio(self, frames1, frames2):
        if not frames1 and not frames2: return []
        if not frames1: return frames2
        if not frames2: return frames1
        min_len = min(len(frames1), len(frames2))
        mixed = []
        for f1, f2 in zip(frames1[:min_len], frames2[:min_len]):
            arr1 = np.frombuffer(f1, dtype=np.int16)
            arr2 = np.frombuffer(f2, dtype=np.int16)
            mixed_arr = np.clip((arr1.astype(np.int32) + arr2.astype(np.int32)) // 2, -32768, 32767).astype(np.int16)
            mixed.append(mixed_arr.tobytes())
        return mixed

    def _process_dual(self):
        try:
            import time
            time.sleep(0.2)
            mixed_frames = self._mix_audio(self.system_frames, self.mic_frames)
            
            if not mixed_frames:
                self.root.after(0, lambda: self.update_result("", no_audio=True))
                return
            
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(mixed_frames))
            buffer.name = "audio.wav"
            buffer.seek(0) 

            # Whisper
            transcription = self.client.audio.transcriptions.create(
                file=(buffer.name, buffer.read()), model="whisper-large-v3-turbo", 
                response_format="json", language="vi", temperature=0.0 
            )
            text = transcription.text.strip()
            
            if not text: 
                self.root.after(0, lambda: self.update_result("", no_audio=True))
                return

            self.root.after(0, lambda: self.format_and_insert("User", text))
            self.server.send_user_message(text)
            self.process_text_input(text)
            
        except Exception as e:
            self.root.after(0, lambda: self.status_lbl.config(text="❌ Error"))
            self.server.emit_chunk(f"\n❌ Error: {str(e)}")

    def update_result(self, text, no_audio=False):
        if no_audio:
            self.status_lbl.config(text="⚠️ No Audio", fg='#555')
            self.root.after(1000, lambda: self.status_lbl.config(text="● Idle"))
    
    def on_closing(self):
        """Cleanup khi đóng chương trình"""
        print("\n🔴 Shutting down...")
        self.stop_event.set()
        self.is_recording = False
        self.is_processing_image = False
        self.is_screenshot_mode = False
        try:
            self.audio.terminate()
        except:
            pass
        self.root.quit()
        self.root.destroy()
        os._exit(0)

# ===================== MAIN =====================
app = SystemAudioControl()
current_keys = set()

def on_press(key):
    current_keys.add(key)
    
    # Check Modifiers
    ctrl = any(k in current_keys for k in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r])
    shift = any(k in current_keys for k in [keyboard.Key.shift_l, keyboard.Key.shift_r])
    alt = any(k in current_keys for k in [keyboard.Key.alt_l, keyboard.Key.alt_r])
    
    if ctrl and shift and alt:
        # Check 'R' for Record
        if hasattr(key, 'char') and key.char == 'r':
            app.start_recording()
        elif hasattr(key, 'vk') and key.vk == 82: 
            app.start_recording()
            
        # Check 'S' for Scan (Image)
        if hasattr(key, 'char') and key.char == 's':
            app.trigger_image_scan()
        elif hasattr(key, 'vk') and key.vk == 83: 
            app.trigger_image_scan()
        
        # Check 'Z' for Screenshot (MỚI)
        if hasattr(key, 'char') and key.char == 'z':
            app.trigger_screenshot()
        elif hasattr(key, 'vk') and key.vk == 90:  # VK code for 'Z'
            app.trigger_screenshot()

def on_release(key):
    try:
        if key in current_keys: current_keys.remove(key)
    except: pass
    
    # Release 'R' stops recording
    if (hasattr(key, 'char') and key.char=='r') or (hasattr(key, 'vk') and key.vk==82):
        app.stop_recording()
    
    # Release 'Z' finishes screenshot (MỚI)
    if (hasattr(key, 'char') and key.char=='z') or (hasattr(key, 'vk') and key.vk==90):
        app.finish_screenshot()

if __name__ == "__main__":
    if "gsk_" not in GROQ_API_KEY: print("⚠️ Check Groq Key")
    
    # Kiểm tra admin
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("⚠️ CẢNH BÁO: CHƯA CHẠY QUYỀN ADMIN. CÓ THỂ KHÔNG NHẬN PHÍM.")
    
    Thread(target=app.server.run, daemon=True).start()
    
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    
    print(f"🚀 Controller Active on Port {MOBILE_PORT}")
    print(f"📸 Screenshot Hotkey: Ctrl+Shift+Alt+Z (drag to select area)")
    print(f"💡 Nhấn Ctrl+C hoặc đóng cửa sổ để thoát\n")
    
    try:
        app.setup_ui()
        app.root.mainloop()
    except KeyboardInterrupt:
        print("\n\n🔴 Đã nhận Ctrl+C, đang thoát...")
        app.on_closing()
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        app.on_closing()