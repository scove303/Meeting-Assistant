import sys
import json
import base64
import requests
import webview
import os
import socket
import logging
from io import BytesIO
from PIL import Image, ImageGrab
from pynput import keyboard
import pyautogui
from threading import Thread
import time

# --- THƯ VIỆN WEB SERVER CHO ĐIỆN THOẠI ---
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# Tắt log rác của Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ===================== CẤU HÌNH =====================
CONFIG_FILE = 'math_solver_config.json'
DEFAULT_CONFIG = {
    "width_cm": 10,
    "height_cm": 6,
    "debug_mode": False,
    "engine": "gemini"
}

# --- API KEYS ---
GEMINI_API_KEY = 'AIzaSyBG8PO_PjKFQc2oQI2GOiVGp5STu3bzAAs' 
GEMINI_MODEL = 'gemini-3-flash-preview'
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2-vision"

SYSTEM_PROMPT = """
Bạn là một trợ lý Toán học và Khoa học chuyên nghiệp.
QUY TẮC:
1. Luôn trả lời bằng Tiếng Việt.
2. Dùng LaTeX cho công thức: $...$ (inline), $$...$$ (block).
3. Trình bày ngắn gọn, từng bước (Step-by-step).
4. Bôi đậm kết quả cuối cùng.
5. Chỉ show phần bài làm only. NO BULLSHIT


Môn học về    PRJ321x.4.0.VN Phát triển ứng dụng Web

Các câu hỏi liên quan:
PRJ321_o1x 	Hiểu rõ và nắm vững khái niệm về Servlet và JSP
PRJ321_o2x 	Cài đặt môi trường phát triển ứng dụng Web
PRJ321_o3x 	Hiểu được cấu trúc của ứng dụng Web bằng Java
PRJ321_o4x 	Nắm được kiến thức và thực hành về câu lệnh và biểu thức trong JSP
PRJ321_o5x 	Vận dụng được kiến thức để thực hành với Script trong JSP
PRJ321_o6x 	Nắm được kiến thức và thực hành về khai báo biến, xây dựng đối tượng và thêm file trong JSP
PRJ321_o7x 	Hiểu rõ về khái niệm và vai trò của các đối tượng trong HTML Form
PRJ321_o8x 	Hiểu được khái niệm và vai trò của các đối tượng Drop Down List, Radio Buttons và Checkboxes trong JSP
PRJ321_o9x 	Hiểu được kiến thức liên quan tới trạng thái của người dùng khi thao tác và sử dụng Session
PRJ321_o10x 	Sử dụng linh hoạt các đối tượng trong Session
PRJ321_o11x 	Hiểu được kiến thức và thực hành đối với Cookies trong JSP
PRJ321_o12x 	Hiểu được khái niệm, vai trò về JSP Tags
PRJ321_o13x 	Sử dụng các kiến thức trong JSP Tags: vòng lặp, kiểm tra điều kiện,...
PRJ321_o14x 	Vận dụng được kiến thức trong JSP Function Tags để trong thao tác về: length, toUpperCase, startsWith, split, join,...
PRJ321_o15x 	Hiểu rõ khái niệm và phân biệt sự khác nhau giữa Servlets và JSP
PRJ321_o16x 	Sử dụng linh hoạt về đọc dữ liệu của HTML Form cùng với Servlets
PRJ321_o17x 	Sử dụng các giao thức HTTP trong Servlet: GET, POST,...
PRJ321_o18x 	Hiểu rõ kiến thức và thực hành cùng với Servlets và JSP trong MVC
PRJ321_o19x 	Sử dụng linh hoạt kiến thức về Servlet để xây dựng ứng dụng Web cùng với JDBC
PRJ321_o20x 	Hiểu rõ được khái niệm về Spring MVC
PRJ321_o21x 	Nắm vững được cách hoạt động, cấu trúc và vai trò của Spring MVC
PRJ321_o22x 	Vận dụng được kiến thức để xây dựng và cấu hình được ứng dụng Web sử dụng Spring MVC
PRJ321_o23x 	Hiểu và thực hành xử lý luồng tương tác giữa Model - View - Controller trong Spring MVC
PRJ321_o24x 	Thành thạo đọc dữ liệu, thêm dữ liệu thông qua Spring Model
PRJ321_o25x 	Phân biệt và sử dụng đúng hai đối tượng: Request Params và Request Mapping
PRJ321_o26x 	Hiểu rõ được khái niệm về Spring MVC Form Tags
PRJ321_o27x 	Thao tác đối với các đối tượng Text Fields, Drop-down Lists, Radio Buttons, Checkboxes trong Spring MVC Form
PRJ321_o28x 	Biết cách thêm ràng buộc dữ liệu (data binding) với các đối tượng trong Spring MVC Form
PRJ321_o29x 	Hiểu rõ về khái niệm Hibernate trong Spring MVC
PRJ321_o30x 	Phân biệt sự khác nhau giữa Hibernate và JDBC trong ứng dụng Java Web
PRJ321_o31x 	Vận dụng Hibernate trong Spring MVC
PRJ321_o32x 	Nắm vững khái niệm và thực hành được với Hibernate Annotations
PRJ321_o33x 	Thao tác được với việc tạo và lưu với Java Object
PRJ321_o34x 	Nắm vững được kiến thức về Mapping trong Hibernate
PRJ321_o35x 	Sử dụng linh hoạt Mapping trong Hibernate cũng như là các dạng quan hệ tương ứng: @OneToOne, @OneToMay, @ManyToMany
PRJ321_o36x 	Áp dụng được với cơ chế Eager, Lazy và Closing Session trong Spring
PRJ321_o37x 	Vận dụng kiến thức trong việc thao tác với truy vấn HQL
PRJ321_o38x 	Sử dụng những kiến thức để thực hành xây dựng lên một webAPP sử dụng Spring MVC và Hibernate
PRJ321_o39x 	Vận dụng được kết hợp front-end và back-end trong ứng dụng Java Web
"""

# ===================== GIAO DIỆN ĐIỆN THOẠI (HTML) =====================
MOBILE_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Math AI Mobile</title>
    <style>
        body { background-color: #000000; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; font-size: 16px; line-height: 1.6; }
        #status { font-size: 12px; color: #81C784; text-align: center; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 10px; }
        .content-box { min-height: 200px; }
        
        /* Message Styles */
        .msg { padding: 15px; border-radius: 12px; margin-bottom: 15px; animation: fadeIn 0.3s ease; }
        .ai { background: #1a1a1a; border-left: 4px solid #FFCA28; box-shadow: 0 2px 10px rgba(255,255,255,0.05); }
        .error { border-left: 4px solid #E57373; background: #2a1a1a; }
        
        /* Typing cursor */
        .cursor::after { content: "▋"; color: #FFCA28; animation: blink 1s infinite; margin-left: 2px; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

        /* MathJax Custom */
        mjx-container { color: #FFD54F !important; font-size: 110% !important; overflow-x: auto; overflow-y: hidden; }
        img { max-width: 100%; border-radius: 8px; margin-top: 10px; }
        h1, h2, h3 { color: #81C784; margin-top: 15px; }
        strong { color: #fff; font-weight: 700; }
    </style>
    <script>MathJax={tex:{inlineMath:[['$','$']],displayMath:[['$$','$$']]},svg:{fontCache:'global'}};</script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <div id="status">● Đã kết nối với PC</div>
    <div id="container" class="content-box">
        <div class="msg ai">Chào bạn! Kết quả từ PC sẽ hiện tại đây.</div>
    </div>

    <script>
        var socket = io();
        var container = document.getElementById('container');
        var currentDiv = null;
        var buffer = "";

        socket.on('connect', function() {
            document.getElementById('status').innerText = "● Đã kết nối với PC (Online)";
            document.getElementById('status').style.color = "#81C784";
        });

        socket.on('disconnect', function() {
            document.getElementById('status').innerText = "○ Mất kết nối PC...";
            document.getElementById('status').style.color = "#E57373";
        });

        // Bắt đầu câu trả lời mới
        socket.on('start_response', function() {
            container.innerHTML = ""; // Xóa cái cũ
            currentDiv = document.createElement('div');
            currentDiv.className = 'msg ai cursor';
            container.appendChild(currentDiv);
            buffer = "";
        });

        // Nhận từng chữ (Streaming)
        socket.on('stream_chunk', function(data) {
            if (!currentDiv) return;
            // Xử lý ký tự đặc biệt HTML
            let safeText = data.text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            buffer += safeText;
            currentDiv.innerHTML = buffer.replace(/\\n/g, "<br>");
            window.scrollTo(0, document.body.scrollHeight);
        });

        // Kết thúc câu trả lời (Render đẹp)
        socket.on('finish_response', function(data) {
            if (!currentDiv) return;
            currentDiv.classList.remove('cursor');
            currentDiv.innerHTML = data.html;
            MathJax.typesetPromise([currentDiv]);
            window.scrollTo(0, document.body.scrollHeight);
        });
        
        socket.on('clear_memory', function() {
            container.innerHTML = '<div class="msg ai">🧹 Bộ nhớ đã xóa.</div>';
        });
    </script>
</body>
</html>
"""

# ===================== PC GIAO DIỆN (HTML) =====================
PC_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #1e1e1e; color: #e0e0e0; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        #header { background: #2d2d2d; padding: 10px 15px; border-bottom: 2px solid #3d3d3d; z-index: 10; }
        .header-top { display: flex; justify-content: space-between; align-items: center; }
        .title { font-weight: bold; font-size: 16px; color: #4FC3F7; }
        .mobile-link { font-size: 11px; color: #FFCA28; margin-left: 10px; background: #333; padding: 2px 6px; border-radius: 4px; cursor: pointer;}
        .btn { border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 12px; }
        .btn-settings { background: #546E7A; color: white; }
        .btn-reset { background: #d32f2f; color: white; margin-left: 5px; }
        #settings-panel { background: #252525; padding: 10px; display: none; border-top: 1px solid #444; }
        .control-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; align-items: center; }
        input[type=range] { flex: 1; margin: 0 10px; }
        select { background: #444; color: white; border: none; padding: 4px; }
        .switch { position: relative; display: inline-block; width: 30px; height: 16px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #555; transition: .4s; border-radius: 34px; }
        .slider:before { position: absolute; content: ""; height: 10px; width: 10px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: #4CAF50; }
        input:checked + .slider:before { transform: translateX(14px); }
        #chat-container { flex: 1; padding: 20px; overflow-y: auto; scroll-behavior: smooth; display: flex; flex-direction: column; gap: 15px; }
        .message { max-width: 95%; padding: 12px; border-radius: 8px; line-height: 1.5; word-wrap: break-word; font-size: 14px; }
        .user-msg { align-self: flex-end; background: #00695C; color: white; }
        .ai-msg { align-self: flex-start; background: #263238; border-left: 3px solid #FFCA28; }
        .cursor::after { content: "▋"; color: #FFCA28; animation: blink 1s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        mjx-container { color: #FFD54F !important; }
        ::-webkit-scrollbar { width: 6px; background: #1e1e1e; }
        ::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }
    </style>
    <script>MathJax={tex:{inlineMath:[['$','$']],displayMath:[['$$','$$']]},svg:{fontCache:'global'}};</script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
    <div id="header">
        <div class="header-top">
            <div>
                <span class="title">🤖 PC Master</span>
                <span id="mobileIp" class="mobile-link" onclick="copyIp()">📱 Waiting IP...</span>
            </div>
            <div>
                <button class="btn btn-settings" onclick="toggleSettings()">⚙️</button>
                <button class="btn btn-reset" onclick="resetMemory()">🧹</button>
            </div>
        </div>
        <div id="settings-panel">
            <div class="control-row"><span>Engine:</span><select id="es" onchange="upd()"><option value="gemini">Gemini Cloud</option><option value="ollama">Ollama (GPU)</option></select></div>
            <div class="control-row"><span>Rộng:</span><input type="range" id="wIn" min="2" max="25" step="0.5" oninput="upd()"><span id="wV" style="width:30px;text-align:right;color:#FF9800"></span></div>
            <div class="control-row"><span>Cao:</span><input type="range" id="hIn" min="2" max="25" step="0.5" oninput="upd()"><span id="hV" style="width:30px;text-align:right;color:#FF9800"></span></div>
            <div class="control-row"><span>Xem ảnh:</span><label class="switch"><input type="checkbox" id="dCh" onchange="upd()"><span class="slider round"></span></label></div>
        </div>
    </div>
    <div id="chat-container"><div class="message ai-msg">⚡ <strong>Hệ thống sẵn sàng!</strong><br>Kết nối điện thoại theo IP ở trên.<br>Ctrl+Shift+Alt+S để chụp.</div></div>

    <script>
        let curAi = null; let buf = "";
        window.addEventListener('pywebviewready', function() {
            pywebview.api.get_config().then(function(c) {
                document.getElementById('wIn').value = c.width_cm; document.getElementById('wV').innerText = c.width_cm;
                document.getElementById('hIn').value = c.height_cm; document.getElementById('hV').innerText = c.height_cm;
                document.getElementById('dCh').checked = c.debug_mode; document.getElementById('es').value = c.engine || 'gemini';
                pywebview.api.get_local_ip().then(function(ip) { document.getElementById('mobileIp').innerText = "📱 " + ip + ":5000"; });
            });
        });
        function toggleSettings() { var p = document.getElementById('settings-panel'); p.style.display = p.style.display==='block'?'none':'block'; }
        function upd() { pywebview.api.save_config_backend(parseFloat(document.getElementById('wIn').value), parseFloat(document.getElementById('hIn').value), document.getElementById('dCh').checked, document.getElementById('es').value); document.getElementById('wV').innerText = document.getElementById('wIn').value; document.getElementById('hV').innerText = document.getElementById('hIn').value; }
        function appendUser() { var c = document.getElementById('chat-container'), d = document.createElement('div'); d.className = 'message user-msg'; d.innerHTML = '🚀 <em>Đang xử lý...</em>'; c.appendChild(d); window.scrollTo(0, document.body.scrollHeight); }
        function startAi() { var c = document.getElementById('chat-container'); curAi = document.createElement('div'); curAi.className = 'message ai-msg cursor'; c.appendChild(curAi); buf = ""; window.scrollTo(0, document.body.scrollHeight); }
        function streamChunk(t) { if (!curAi) return; buf += t.replace(/</g, "&lt;").replace(/>/g, "&gt;"); curAi.innerHTML = buf.replace(/\\n/g, "<br>"); window.scrollTo(0, document.body.scrollHeight); }
        function finishAi(h) { if (!curAi) return; curAi.classList.remove('cursor'); curAi.innerHTML = h; MathJax.typesetPromise([curAi]); curAi = null; window.scrollTo(0, document.body.scrollHeight); }
        function showError(m) { var c = document.getElementById('chat-container'), d = document.createElement('div'); d.className = 'message ai-msg'; d.style.borderLeftColor = "red"; d.innerHTML = "❌ " + m; c.appendChild(d); }
        function clearChat() { document.getElementById('chat-container').innerHTML = '<div class="message ai-msg">🧹 Memory Cleared.</div>'; }
        function resetMemory() { pywebview.api.reset_memory_backend(); }
        function copyIp() { alert("Nhập địa chỉ IP này vào trình duyệt trên điện thoại!"); }
    </script>
</body>
</html>
"""

# ===================== CLASS SERVER =====================
class MobileServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Route trang chủ
        @self.app.route('/')
        def index():
            return render_template_string(MOBILE_HTML)
        
    def run_server(self):
        # Chạy server ở cổng 5000
        self.socketio.run(self.app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

    def emit_start(self):
        self.socketio.emit('start_response')

    def emit_chunk(self, text):
        self.socketio.emit('stream_chunk', {'text': text})

    def emit_finish(self, html):
        self.socketio.emit('finish_response', {'html': html})
        
    def emit_clear(self):
        self.socketio.emit('clear_memory')

# ===================== CLASS LOGIC CHÍNH =====================
class MathAssistant:
    def __init__(self):
        self.window = None
        self.history = []
        self.is_processing = False
        self.server = MobileServer() # Khởi tạo Server
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f: self.config = json.load(f)
            except: self.config = DEFAULT_CONFIG
        else:
            self.config = DEFAULT_CONFIG
            self.save_config_file()

    def save_config_file(self):
        with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f)

    def get_config(self): return self.config
    
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except: return "127.0.0.1"

    def save_config_backend(self, w, h, d, e):
        self.config.update({"width_cm": w, "height_cm": h, "debug_mode": d, "engine": e})
        self.save_config_file()

    def reset_memory_backend(self):
        self.history = []
        if self.window: self.window.evaluate_js('clearChat()')
        self.server.emit_clear() # Báo điện thoại xóa luôn

    def optimize_image(self, image):
        try:
            img = image.convert('L')
            if max(img.size) > 700:
                ratio = 700 / max(img.size)
                img = img.resize((int(img.size[0]*ratio), int(img.size[1]*ratio)), Image.Resampling.LANCZOS)
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=50, optimize=True)
            return buffered.getvalue()
        except: return None

    def capture_screen(self):
        try:
            x, y = pyautogui.position()
            dpi = 96
            w_px = int(self.config['width_cm'] * dpi / 2.54)
            h_px = int(self.config['height_cm'] * dpi / 2.54)
            bbox = (max(0, x - w_px//2), max(0, y - h_px//2), x + w_px//2, y + h_px//2)
            screenshot = ImageGrab.grab(bbox=bbox, all_screens=True)
            if self.config['debug_mode']:
                try:
                    fn = "debug_snap.jpg"
                    screenshot.save(fn)
                    os.startfile(fn)
                except: pass
            return screenshot
        except: return None

    def markdown_to_html(self, text):
        import re
        html = text.replace('<', '&lt;').replace('>', '&gt;')
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'^### (.*)', r'<h3>\1</h3>', html, flags=re.M)
        html = re.sub(r'^## (.*)', r'<h2>\1</h2>', html, flags=re.M)
        html = html.replace('\n', '<br>')
        return html

    def solve_stream(self):
        if self.is_processing: return
        self.is_processing = True
        
        # 1. UI PC báo xử lý
        if self.window:
            self.window.evaluate_js("appendUser()")
            self.window.evaluate_js("startAi()")
        
        # 2. Báo điện thoại chuẩn bị nhận
        self.server.emit_start()

        try:
            image = self.capture_screen()
            if not image: raise Exception("Lỗi chụp")
            img_bytes = self.optimize_image(image)
            img_base64 = base64.b64encode(img_bytes).decode()
            
            full_text = ""
            engine = self.config.get('engine', 'gemini')

            # --- OLLAMA STREAMING ---
            if engine == 'ollama':
                payload = { "model": OLLAMA_MODEL, "prompt": SYSTEM_PROMPT+"\nGiải bài:", "images": [img_base64], "stream": True }
                response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)
                for line in response.iter_lines():
                    if line:
                        try:
                            obj = json.loads(line.decode())
                            if 'response' in obj:
                                chunk = obj['response']
                                full_text += chunk
                                # Stream PC
                                if self.window: self.window.evaluate_js(f"streamChunk({json.dumps(chunk)})")
                                # Stream Phone
                                self.server.emit_chunk(chunk)
                        except: pass
            
            # --- GEMINI (SIMULATED STREAMING) ---
            else:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
                user_msg = {"role": "user", "parts": [{"text": "Giải."}, {"inline_data": {"mime_type": "image/jpeg", "data": img_base64}}]}
                payload = { "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]}, "contents": self.history + [user_msg], "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4096} }
                response = requests.post(url, json=payload, timeout=20)
                if response.status_code == 200:
                    full_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                    chunk_size = 15
                    for i in range(0, len(full_text), chunk_size):
                        chunk = full_text[i:i+chunk_size]
                        # Stream PC
                        if self.window: self.window.evaluate_js(f"streamChunk({json.dumps(chunk)})")
                        # Stream Phone
                        self.server.emit_chunk(chunk)
                        time.sleep(0.01) # Delay nhẹ để điện thoại render kịp
                else: full_text = "Lỗi API"

            if full_text:
                self.history.append({"role": "user", "parts": [{"text": "..."}]})
                self.history.append({"role": "model", "parts": [{"text": full_text}]})
                if len(self.history) > 6: self.history = self.history[-6:]

            # --- KẾT THÚC ---
            html_final = self.markdown_to_html(full_text)
            safe_html = json.dumps(html_final)
            # Update PC
            if self.window: self.window.evaluate_js(f"finishAi({safe_html})")
            # Update Phone
            self.server.emit_finish(html_final)

        except Exception as e:
            err = json.dumps(str(e))
            if self.window: self.window.evaluate_js(f"showError({err})")
            self.server.emit_chunk(f"\n❌ Lỗi: {str(e)}")
        
        self.is_processing = False

app = MathAssistant()

def on_hotkey(): Thread(target=app.solve_stream).start()

def start_hotkey():
    with keyboard.GlobalHotKeys({'<ctrl>+<shift>+<alt>+s': on_hotkey}) as h: h.join()

if __name__ == '__main__':
    # 1. Chạy Web Server (Thread riêng)
    server_thread = Thread(target=app.server.run_server, daemon=True)
    server_thread.start()
    
    # 2. Chạy Hotkey Listener (Thread riêng)
    hk_thread = Thread(target=start_hotkey, daemon=True)
    hk_thread.start()
    
    print(f"🚀 PC & Mobile Server Started!")
    
    # 3. Chạy GUI
    app.window = webview.create_window('Math AI Pro Ecosystem', html=PC_HTML, width=480, height=650, on_top=True, js_api=app)
    webview.start()