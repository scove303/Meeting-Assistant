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

# --- MATPLOTLIB CHO LATEX RENDERING ---
import matplotlib
matplotlib.use('Agg')  # Backend không cần GUI
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import mathtext as mtext

# --- THƯ VIỆN WEB SERVER ---
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit

# Tắt log rác Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ===================== CẤU HÌNH =====================
# API Keys
GROQ_API_KEYS = [
    "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",
    "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",
    "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",
]
GEMINI_API_KEY = 'AIzaSyBG8PO_PjKFQc2oQI2GOiVGp5STu3bzAAs' 
GEMINI_MODEL = 'gemini-3-flash-preview' 

# (Tuỳ chọn) Mathpix API dùng để đọc công thức toán học siêu chính xác
# Lấy key tại: https://mathpix.com/
MATHPIX_APP_ID = ""
MATHPIX_APP_KEY = ""

MOBILE_PORT = 5001

# Screenshot Config
SCREENSHOT_HOTKEY = 'z'  # Sẽ kết hợp với Ctrl+Shift+Alt
SCREENSHOT_SAVE_PATH = "screenshots"
SCREENSHOT_QUALITY = 100

if not os.path.exists(SCREENSHOT_SAVE_PATH):
    os.makedirs(SCREENSHOT_SAVE_PATH)

# PLACEHOLDER SYSTEM PROMPT
SYSTEM_PROMPT = r"""
Bạn là một trợ lý giải Toán theo phong cách "Visual Note" (Ghi chú trực quan).
Đối tượng: Học sinh lớp 12 mất gốc, hay quên công thức.

MỤC TIÊU:
Tối đa hóa khả năng "nhìn lướt" (scannability). KHÔNG viết đoạn văn. KHÔNG giải thích dông dài. Chỉ dùng từ khóa, công thức và ký hiệu.

QUY TẮC HIỂN THỊ (NGHIÊM NGẶT):
1.  **Format**: Sử dụng cấu trúc khối, gạch đầu dòng và mũi tên ($\to, \Rightarrow, \downarrow$) thay vì lời nói.
2.  **Công thức (Quan trọng nhất)**: Luôn để công thức trong block trích dẫn (`>`) ngay trước khi áp dụng.
3.  **Phong cách giải**: 
    - Dòng 1: Xác định dạng bài (Ví dụ: Dạng $0/0$, Tích phân từng phần...).
    - Các bước: Trình bày dạng dòng chảy.
    - Toán: Viết tường minh, không làm tắt bước thay số.

CẤU TRÚC BÀI LÀM:
### 📌 [Tên dạng bài toán]

> **💡 Công thức cần nhớ:**
> [Ghi công thức tổng quát $y = f(x)...$ ở đây]

**Bước [n]: [Hành động ngắn gọn]**
$$ [Biểu thức Toán học] $$
$\downarrow$ *[Giải thích siêu ngắn bằng 3-5 từ hoặc mũi tên]*
$$ [Biểu thức sau biến đổi] $$

---

**🏁 Kết quả: [Đáp án]**

VÍ DỤ MẪU (Bắt buộc làm theo style này):

User: Tính $I = \int x \ln x \, dx$

AI:

### 📌 Tích phân từng phần

> **💡 Công thức:**
> $\int u \, dv = u.v - \int v \, du$
> (Mẹo: Nhất Lô, Nhì Đa, Tam Lượng, Tứ Mũ $\to$ Đặt $u = \ln x$)

**Bước 1: Đặt $u$ và $dv$**

$$
\begin{cases} u = \ln x \\ dv = x \, dx \end{cases}
\Rightarrow
\begin{cases} du = \frac{1}{x} \, dx \\ v = \frac{x^2}{2} \end{cases}
$$

**Bước 2: Thay vào công thức**
$$ I = \underbrace{\ln x}_{u} \cdot \underbrace{\frac{x^2}{2}}_{v} - \int \underbrace{\frac{x^2}{2}}_{v} \cdot \underbrace{\frac{1}{x} \, dx}_{du} $$

**Bước 3: Rút gọn và tính**
$$ I = \frac{x^2}{2}\ln x - \frac{1}{2} \int x \, dx $$
$\downarrow$ *Áp dụng $\int x dx = \frac{x^2}{2}$*
$$ I = \frac{x^2}{2}\ln x - \frac{1}{2} \cdot \frac{x^2}{2} + C $$

---

**🏁 Kết quả: $I = \frac{x^2}{2}\ln x - \frac{x^4}{4} + C$**

các chuẩn kiến thức, kỹ năng đầu ra như sau:

1. Hiểu được quy tắc L'Hopistal

- Hiểu được quy tắc dạng 0/0

- Hiểu được quy tắc dạng ∞/∞

- Hiểu được các dạng khác của quy tắc L'Hopistal

2. Hiểu được những khái niệm liên quan đến phương trình tham số như:

- Phương trình tham số của quỹ đạo

- Hệ số góc của đường cong

- Vị trí và vận tốc, gia tốc

3. Hiểu được những khái niệm liên quan đến ứng dụng của đạo hàm như:

- Tốc độ, quãng đường đi được của vật thể

- Đạo hàm cấp 2 và tính lồi lõm của hàm số

- Gia tốc của vật trong chuyển động

4. Nắm được các khái niệm về chuỗi số:

- Nắm được khái niệm cơ bản về dãy số

- Nắm được khái niệm cơ bản của chuỗi số, thế nào là chuỗi hội tụ và phân kỳ

5. Nắm được cách tính chất của chuỗi chẳng hạn như:

- Tổng các số của một cấp số nhân

- Nắm được chuỗi mũ.

6. Hiểu được khai triển Taylor và Maclaurin của một đa thức.

7. Hiểu được các cách xác định tính hội tụ của chuỗi:

- Kiểm tra tính hội tụ của chuỗi đan dấu

-Kiểm tra tính hội tụ bằng phương pháp phân

8. Hiểu được cách xác định độ sai số khi khai triển chuỗi

9. Vận dụng tính chất của chuỗi trong việc như:

- Tính đạo hàm và tích phân

- Các tính toán thông thường của hàm số

- Khai triển bằng phương pháp thay thế

10. Nắm được công thức độ dài cung

- Công thức độ dài cung

- Độ dài cung của phương trình tham số trong tọa độ cực

11. Hiểu được phương pháp Euler

- Hiểu cách tính phương trình tiếp tuyến tại một điểm

- Hiểu được các khai triển gần đúng tuyến tính của một phương trình tại một điểm

- Giải gần đúng phương trình vi phân bằng phương pháp số

12. Hiểu được tích phân suy rộng định nghĩa, ví dụ

13. Hiểu được các phương pháp kiểm tra tính hội tụ của tích phân suy rộng

14. Hiểu được kỹ thuật tính tích phân ở dạng phân số

- Tính tích phân ở dạng phân số

- Giải phương trình vi phân ở dạng đa thức

15. Hiểu được kỹ thuật tính tích phân từng phần

16. Hiểu được hàm trong tọa độ cực

- Hệ sộ góc trong tọa độ cực

- Diện tích của vùng giới hạn bởi 1 đường trong tọa độ cực

- Diện tích của vùng giới hạn bởi hơn 1 đường trong tọa độ cực
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
        
        # Giữ tham chiếu đến PhotoImage để tránh garbage collection
        self.photo_images = []
        
        # === VARIABLES CHO CẤU HÌNH ẢNH ===
        self.scan_w_var = None
        self.scan_h_var = None
        
        # === WEB SERVER MOBILE ===
        self.server = AudioMobileServer(self)

    def setup_groq(self):
        self.current_groq_key_index = 0
        try:
            self.client = Groq(api_key=GROQ_API_KEYS[self.current_groq_key_index])
        except Exception as e:
            print(f"Groq Init Error: {e}")

    def _call_mathpix(self, img_b64):
        """Gọi Mathpix API để OCR toán học siêu chuẩn"""
        if not MATHPIX_APP_ID or not MATHPIX_APP_KEY:
            return None
        try:
            headers = {
                "app_id": MATHPIX_APP_ID,
                "app_key": MATHPIX_APP_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "src": f"data:image/jpeg;base64,{img_b64}",
                "formats": ["text"]
            }
            resp = requests.post("https://api.mathpix.com/v3/text", json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp.json().get("text", "")
        except Exception as e:
            if self.debug_mode_var.get():
                print(f"Mathpix Error: {e}")
        return None

    def switch_groq_key(self):
        if len(GROQ_API_KEYS) > 1:
            self.current_groq_key_index = (self.current_groq_key_index + 1) % len(GROQ_API_KEYS)
            print(f"🔄 Đã đổi sang Groq API Key khác (Index: {self.current_groq_key_index})")
            self.client = Groq(api_key=GROQ_API_KEYS[self.current_groq_key_index])
            return True
        return False

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
        self.photo_images.clear()  # Giải phóng bộ nhớ ảnh LaTeX
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
            
            # Copy vào clipboard (Người dùng gọi cái này là 'quét')
            self._copy_to_clipboard(img)
            
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

            # Xác định URL và câu hỏi của User
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            user_query = "Hãy đọc và giải quyết yêu cầu/câu hỏi có trong ảnh này."
            if self.conversation_history:
                last_msg = self.conversation_history[-1]
                if last_msg['role'] == 'user':
                    user_query = last_msg['content']

            # Kiểm tra xem có dùng Mathpix không
            mathpix_text = self._call_mathpix(img_b64)
            
            # Mobile UI Start
            self.server.send_user_message(f"📸 Screenshot ({width}x{height}px): {user_query}")
            self.server.emit_start()

            if mathpix_text:
                if self.debug_mode_var.get():
                    print(f"🧮 Mathpix OCR thành công: {mathpix_text}")
                
                # Chuyển qua Groq (Llama) xử lý text thay vì dùng Gemini
                self.root.after(0, lambda: self.status_lbl.config(text="🔄 Solving with Llama...", fg='#569cd6'))
                
                prompt = (
                    f"Tôi đã scan một hình ảnh toán học và đây là kết quả đọc được từ ảnh (định dạng LaTeX):\n"
                    f"```latex\n{mathpix_text}\n```\n\n"
                    f"YÊU CẦU TỪ NGƯỜI DÙNG: {user_query}\n\n"
                    f"Hãy thực hiện yêu cầu trên theo đúng luật của bạn."
                )
                
                # Gọi thẳng Groq bằng cơ chế text
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                messages.extend(self.conversation_history)
                messages.append({"role": "user", "content": prompt})
                
                answer = ""
                max_retries = len(GROQ_API_KEYS)
                for attempt in range(max_retries):
                    try:
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
                                answer += delta
                                self.server.emit_chunk(delta)
                        break
                    except Exception as e:
                        err_str = str(e).lower()
                        if 'rate limit' in err_str or '429' in err_str or 'token' in err_str or 'insufficient' in err_str:
                            if attempt < max_retries - 1 and self.switch_groq_key():
                                retry_msg = "\n\n*[⚠️ Đổi Key API...]*\n\n"
                                answer += retry_msg
                                self.server.emit_chunk(retry_msg)
                                continue
                        raise e
            else:
                self.root.after(0, lambda: self.status_lbl.config(text="🔄 Solving with Gemini...", fg='#569cd6'))
                # Dùng Gemini làm Fallback (Cách cũ) nhưng CẢI TIẾN PROMPT (CoT)
                final_prompt = (
                    f"Dưới đây là các quy tắc và vai trò bạn phải tuân thủ:\n{SYSTEM_PROMPT}\n\n"
                    f"YÊU CẦU CỤ THỂ: {user_query}\n\n"
                    f"NHIỆM VỤ: Dựa trên hình ảnh đính kèm, hãy giải quyết bài toán.\n"
                    f"CHÚ Ý QUAN TRỌNG: Trước khi giải, BẮT BUỘC phải thực hiện bước 'Đọc Đề' để phiên âm chính xác 100% các công thức toán, ma trận, biểu thức có trong ảnh thành LaTeX. Sau khi đã đọc đúng đề, mới bắt đầu giải."
                )

                payload = {
                    "contents": [{
                        "parts": [
                            {"text": final_prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                        ]
                    }]
                }

                if self.debug_mode_var.get():
                    print(f"🤖 Đang gửi đến Gemini API...")
                
                max_gemini_retries = 3
                for attempt in range(max_gemini_retries):
                    try:
                        response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, timeout=45)
                        if response.status_code == 200:
                            break
                        elif response.status_code in [429, 503] and attempt < max_gemini_retries - 1:
                            if self.debug_mode_var.get():
                                print(f"⚠️ Gemini API {response.status_code}, retrying in {2 * (attempt + 1)}s...")
                            time.sleep(2 * (attempt + 1))
                            continue
                        else:
                            raise Exception(f"Gemini API Error: {response.status_code} - {response.text}")
                    except requests.exceptions.Timeout:
                        if attempt < max_gemini_retries - 1:
                            if self.debug_mode_var.get():
                                print(f"⚠️ Gemini API Timeout, retrying in {2 * (attempt + 1)}s...")
                            time.sleep(2 * (attempt + 1))
                            continue
                        raise Exception("Gemini API Timeout sau nhiều lần thử")

                result = response.json()
                answer = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No response')
                
                if self.debug_mode_var.get():
                    print(f"✅ Nhận được phản hồi từ Gemini")
                
                # Fake stream for Gemini
                for chunk in answer.split():
                    self.server.emit_chunk(chunk + " ")
                    time.sleep(0.01)

            # Hiển thị kết quả
            self.root.after(0, lambda: self.status_lbl.config(text="✅ Screenshot Analyzed", fg='#4ec9b0'))
            
            # Format và hiển thị như bình thường
            save_info = f" [Saved: {filename}]" if filename else ""
            self.conversation_history.append({"role": "user", "content": f"[Screenshot {width}x{height}px]{save_info} {user_query}"})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            if len(self.conversation_history) > MAX_HISTORY * 2:
                self.conversation_history = self.conversation_history[-MAX_HISTORY*2:]
            
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
            
            # Copy vào clipboard
            self._copy_to_clipboard(img)
            
            import base64
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=95)
            img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # === CALL GEMINI API ===
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            
            # Xác định câu hỏi của User
            user_query = "Hãy đọc và giải quyết yêu cầu/câu hỏi có trong ảnh này."
            if self.conversation_history:
                last_msg = self.conversation_history[-1]
                if last_msg['role'] == 'user':
                    user_query = last_msg['content']

            # Gọi Mathpix OCR
            mathpix_text = self._call_mathpix(img_b64)

            # === MOBILE RESPONSE START ===
            self.server.send_user_message(f"📸 Image Scan: {user_query}")
            self.server.emit_start()

            if mathpix_text:
                if self.debug_mode_var.get():
                    print(f"🧮 Mathpix OCR thành công: {mathpix_text}")
                
                self.root.after(0, lambda: self.status_lbl.config(text="🔄 Solving with Llama...", fg='#569cd6'))
                
                prompt = (
                    f"Tôi đã scan một hình ảnh toán học và đây là kết quả đọc được từ ảnh (định dạng LaTeX):\n"
                    f"```latex\n{mathpix_text}\n```\n\n"
                    f"YÊU CẦU TỪ NGƯỜI DÙNG: {user_query}\n\n"
                    f"Hãy thực hiện yêu cầu trên theo đúng luật của bạn."
                )
                
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                messages.extend(self.conversation_history)
                messages.append({"role": "user", "content": prompt})
                
                answer = ""
                max_retries = len(GROQ_API_KEYS)
                for attempt in range(max_retries):
                    try:
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
                                answer += delta
                                self.server.emit_chunk(delta)
                        break
                    except Exception as e:
                        err_str = str(e).lower()
                        if 'rate limit' in err_str or '429' in err_str or 'token' in err_str or 'insufficient' in err_str:
                            if attempt < max_retries - 1 and self.switch_groq_key():
                                retry_msg = "\n\n*[⚠️ Đổi Key API...]*\n\n"
                                answer += retry_msg
                                self.server.emit_chunk(retry_msg)
                                continue
                        raise e
            else:
                self.root.after(0, lambda: self.status_lbl.config(text="🔄 Solving with Gemini...", fg='#569cd6'))
                # Gemini Fallback với Chain of Thought Prompt
                final_prompt = (
                    f"Dưới đây là hướng dẫn về vai trò và quy tắc trả lời của bạn:\n{SYSTEM_PROMPT}\n\n"
                    f"YÊU CẦU HIỆN TẠI: {user_query}\n\n"
                    f"NHIỆM VỤ: Dựa trên hình ảnh đính kèm, hãy giải quyết bài toán.\n"
                    f"CHÚ Ý QUAN TRỌNG: Trước khi giải, BẮT BUỘC phải thực hiện bước 'Đọc Đề' để phiên âm chính xác 100% các công thức toán, ma trận, biểu thức có trong ảnh thành LaTeX. Sau khi đã đọc đúng đề, mới bắt đầu giải."
                )

                payload = {
                    "contents": [{
                        "parts": [
                            {"text": final_prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                        ]
                    }]
                }

                max_gemini_retries = 3
                for attempt in range(max_gemini_retries):
                    try:
                        response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, timeout=45)
                        if response.status_code == 200:
                            break
                        elif response.status_code in [429, 503] and attempt < max_gemini_retries - 1:
                            if self.debug_mode_var.get():
                                print(f"⚠️ Gemini API {response.status_code}, retrying in {2 * (attempt + 1)}s...")
                            time.sleep(2 * (attempt + 1))
                            continue
                        else:
                            raise Exception(f"Gemini API Error: {response.status_code} - {response.text}")
                    except requests.exceptions.Timeout:
                        if attempt < max_gemini_retries - 1:
                            if self.debug_mode_var.get():
                                print(f"⚠️ Gemini API Timeout, retrying in {2 * (attempt + 1)}s...")
                            time.sleep(2 * (attempt + 1))
                            continue
                        raise Exception("Gemini API Timeout sau nhiều lần thử")

                result = response.json()
                answer = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No response')
                
                # Stream từng từ cho Gemini Fallback
                for chunk in answer.split():
                    self.server.emit_chunk(chunk + " ")
                    time.sleep(0.01)

            # Cập nhật trạng thái
            self.root.after(0, lambda: self.status_lbl.config(text="✅ Scan Complete", fg='#4ec9b0'))
            
            # Lưu vào lịch sử (Lưu user_query gốc để tránh làm rác lịch sử bằng SYSTEM_PROMPT)
            self.conversation_history.append({"role": "user", "content": f"[Image Scan] {user_query}"})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            if len(self.conversation_history) > MAX_HISTORY * 2:
                self.conversation_history = self.conversation_history[-MAX_HISTORY*2:]
            
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
            max_retries = len(GROQ_API_KEYS)
            for attempt in range(max_retries):
                try:
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
                    break # Success
                except Exception as e:
                    err_str = str(e).lower()
                    if 'rate limit' in err_str or '429' in err_str or 'token' in err_str or 'insufficient' in err_str:
                        if attempt < max_retries - 1 and self.switch_groq_key():
                            retry_msg = "\n\n*[⚠️ API Key hiện tại đã hết token, đang tự động đổi Key khác...]*\n\n"
                            full_answer += retry_msg
                            self.server.emit_chunk(retry_msg)
                            continue
                    raise e

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

    # === LATEX RENDERING ===
    def render_latex_image(self, latex_str, display=False):
        """
        Render LaTeX thanh anh PNG bang matplotlib mathtext.
        Tra ve tk.PhotoImage hoac None neu loi.
        """
        try:
            expr = latex_str.strip()
            if not expr:
                return None
            
            fontsize = 22 if display else 16
            dpi = 150
            bg_color = '#1e1e1e'
            bg_rgb = (30, 30, 30)  # #1e1e1e tuong duong
            
            # Render vao figure lon
            fig, ax = plt.subplots(figsize=(20, 3))
            fig.patch.set_facecolor(bg_color)
            ax.set_axis_off()
            ax.set_facecolor(bg_color)
            ax.text(
                0.5, 0.5, f'${expr}$',
                fontsize=fontsize, color='#e8c77a',
                ha='center', va='center',
                transform=ax.transAxes, usetex=False
            )
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=dpi,
                        facecolor=bg_color, edgecolor='none')
            plt.close(fig)
            buf.seek(0)
            
            # Auto-crop bang PIL: loai bo vung nen toi
            pil_img = Image.open(buf).convert('RGB')
            
            # Tao mask: pixel khac mau nen la noi dung
            import numpy as np
            arr = np.array(pil_img)
            mask = ~(
                (arr[:,:,0] == bg_rgb[0]) &
                (arr[:,:,1] == bg_rgb[1]) &
                (arr[:,:,2] == bg_rgb[2])
            )
            rows = np.any(mask, axis=1)
            cols = np.any(mask, axis=0)
            if not rows.any():
                # Fallback neu khong tim thay noi dung
                return None
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]
            
            # Them padding
            pad_px = 10 if display else 7
            h, w = arr.shape[:2]
            rmin = max(0, rmin - pad_px)
            rmax = min(h - 1, rmax + pad_px)
            cmin = max(0, cmin - pad_px)
            cmax = min(w - 1, cmax + pad_px)
            
            cropped = pil_img.crop((cmin, rmin, cmax + 1, rmax + 1))
            
            # Scale len 2x de doc duoc tren man hinh (Tkinter hien thi 1:1 pixel)
            scale = 2
            new_w = cropped.width * scale
            new_h = cropped.height * scale
            cropped = cropped.resize((new_w, new_h), Image.LANCZOS)
            
            import base64
            out_buf = io.BytesIO()
            cropped.save(out_buf, format='PNG')
            b64_data = base64.b64encode(out_buf.getvalue()).decode('utf-8')
            tk_img = tk.PhotoImage(data=b64_data)
            return tk_img
            
        except Exception as e:
            try:
                plt.close('all')
            except:
                pass
            return None

    def _parse_line_with_latex(self, line):
        """
        Parse một dòng text thành danh sách segments:
        [('text', 'nội dung'), ('latex_inline', 'expr'), ...]
        """
        segments = []
        # Pattern cho inline math: $...$ (không phải $$)
        pattern = re.compile(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)')
        last_end = 0
        for m in pattern.finditer(line):
            if m.start() > last_end:
                segments.append(('text', line[last_end:m.start()]))
            segments.append(('latex_inline', m.group(1)))
            last_end = m.end()
        if last_end < len(line):
            segments.append(('text', line[last_end:]))
        return segments if segments else [('text', line)]

    def insert_formatted_text_to_pc(self, text):
        """Insert formatted text vào PC text area với hỗ trợ render LaTeX"""
        
        # Xử lý display math blocks $$...$$ trước (multiline)
        # Tách text thành các đoạn: text thường và display math blocks
        display_pattern = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
        
        # Cũng xử lý \[...\] display math
        display_pattern2 = re.compile(r'\\\[(.+?)\\\]', re.DOTALL)
        
        # Thay thế các cặp \[...\] bằng $$...$$ để xử lý thống nhất
        text = display_pattern2.sub(r'$$\1$$', text)
        
        # Tách thành blocks
        parts = display_pattern.split(text)
        # parts sẽ là: [text, math, text, math, text, ...] do split với capture group
        
        in_code_block = False
        
        for i, part in enumerate(parts):
            if i % 2 == 1:
                # Đây là display math ($$...$$)
                tk_img = self.render_latex_image(part.strip(), display=True)
                if tk_img:
                    self.photo_images.append(tk_img)  # Giữ tham chiếu!
                    self.text_area.insert(tk.END, '\n')
                    self.text_area.image_create(tk.END, image=tk_img, padx=10, pady=4)
                    self.text_area.insert(tk.END, '\n')
                else:
                    # Fallback: hiển thị text thô
                    self.text_area.insert(tk.END, f'  [{part.strip()}]\n', 'code')
            else:
                # Text thường — xử lý từng dòng
                lines = part.split('\n')
                for line in lines:
                    stripped = line.strip()
                    
                    # Toggle code block
                    if stripped.startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    
                    if in_code_block:
                        self.text_area.insert(tk.END, line + '\n', 'code')
                        continue
                    
                    # Headers
                    if line.startswith('### '):
                        self._insert_line_with_inline_latex(line[4:].strip(), 'header')
                        continue
                    elif line.startswith('## '):
                        self._insert_line_with_inline_latex(line[3:].strip(), 'header')
                        continue
                    elif line.startswith('# '):
                        self._insert_line_with_inline_latex(line[2:].strip(), 'header')
                        continue
                    
                    # Dòng trống
                    if not stripped:
                        self.text_area.insert(tk.END, '\n')
                        continue
                    
                    # Separator ---
                    if stripped in ('---', '___', '***'):
                        self.text_area.insert(tk.END, '  ' + '─' * 36 + '\n', 'separator')
                        continue
                    
                    # Dòng có bold + inline latex hỗn hợp
                    self._insert_rich_line(line)

    def _insert_line_with_inline_latex(self, line, base_tag='normal_text'):
        """Insert một dòng có thể chứa inline $...$ LaTeX"""
        # Xử lý bold trước
        bold_parts = re.split(r'(\*\*[^*]+\*\*)', line)
        for bp in bold_parts:
            if bp.startswith('**') and bp.endswith('**'):
                inner = bp[2:-2]
                segs = self._parse_line_with_latex(inner)
                for stype, sval in segs:
                    if stype == 'latex_inline':
                        img = self.render_latex_image(sval, display=False)
                        if img:
                            self.photo_images.append(img)
                            self.text_area.image_create(tk.END, image=img, pady=1)
                        else:
                            self.text_area.insert(tk.END, f'${sval}$', 'bold')
                    else:
                        self.text_area.insert(tk.END, sval, 'bold')
            else:
                segs = self._parse_line_with_latex(bp)
                for stype, sval in segs:
                    if stype == 'latex_inline':
                        img = self.render_latex_image(sval, display=False)
                        if img:
                            self.photo_images.append(img)
                            self.text_area.image_create(tk.END, image=img, pady=1)
                        else:
                            self.text_area.insert(tk.END, f'${sval}$', base_tag)
                    else:
                        self.text_area.insert(tk.END, sval, base_tag)
        self.text_area.insert(tk.END, '\n')

    def _insert_rich_line(self, line):
        """Insert dòng với bold, inline code, inline LaTeX"""
        # Tách bold (**...**) và inline code (`...`) và inline math ($...$)
        token_pattern = re.compile(
            r'(\*\*[^*]+\*\*'           # **bold**
            r'|`[^`]+`'                  # `code`
            r'|(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)'  # $inline math$
            r')'
        )
        parts = token_pattern.split(line)
        for part in parts:
            if not part:
                continue
            if part.startswith('**') and part.endswith('**'):
                self.text_area.insert(tk.END, part[2:-2], 'bold')
            elif part.startswith('`') and part.endswith('`'):
                self.text_area.insert(tk.END, part[1:-1], 'code')
            elif part.startswith('$') and part.endswith('$') and len(part) > 2:
                expr = part[1:-1]
                img = self.render_latex_image(expr, display=False)
                if img:
                    self.photo_images.append(img)
                    self.text_area.image_create(tk.END, image=img, pady=1)
                else:
                    self.text_area.insert(tk.END, part, 'normal_text')
            else:
                self.text_area.insert(tk.END, part, 'normal_text')
        self.text_area.insert(tk.END, '\n')

    # === CORE HELPERS ===
    def _copy_to_clipboard(self, img):
        """Sao chép ảnh vào Clipboard của Windows"""
        try:
            import tempfile
            import subprocess
            import os
            
            # Lưu tạm thành file BMP để Powershell đọc (chắc chắn nhất)
            temp_path = os.path.join(tempfile.gettempdir(), "clipboard_temp.bmp")
            img.convert("RGB").save(temp_path, "BMP")
            
            ps_script = f"""
            Add-Type -AssemblyName System.Windows.Forms;
            $img = [System.Drawing.Image]::FromFile('{temp_path}');
            [System.Windows.Forms.Clipboard]::SetImage($img);
            $img.Dispose();
            """
            
            CREATE_NO_WINDOW = 0x08000000
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], 
                           creationflags=CREATE_NO_WINDOW)
            
            try:
                os.remove(temp_path)
            except:
                pass
                
            if self.debug_mode_var.get():
                print("📋 Đã copy ảnh vào Clipboard bằng Powershell")
        except Exception as e:
            if self.debug_mode_var.get():
                print(f"Lỗi khi copy vào Clipboard: {e}")

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
            text = ""
            max_retries = len(GROQ_API_KEYS)
            for attempt in range(max_retries):
                try:
                    transcription = self.client.audio.transcriptions.create(
                        file=(buffer.name, buffer.read()), model="whisper-large-v3-turbo", 
                        response_format="json", language="vi", temperature=0.0 
                    )
                    text = transcription.text.strip()
                    break
                except Exception as e:
                    err_str = str(e).lower()
                    if 'rate limit' in err_str or '429' in err_str or 'token' in err_str or 'insufficient' in err_str:
                        if attempt < max_retries - 1 and self.switch_groq_key():
                            buffer.seek(0)
                            continue
                    raise e
            
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
    if not any("gsk_" in key for key in GROQ_API_KEYS): print("⚠️ Check Groq Keys")
    
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