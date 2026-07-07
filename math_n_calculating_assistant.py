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

# --- THÊM MODULE QUẢN LÝ TRẠNG THÁI CHUNG ---
import shared_state

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
# Lưu ý: Bạn nên bảo mật API Key này.
GEMINI_API_KEY = 'AIzaSyBG8PO_PjKFQc2oQI2GOiVGp5STu3bzAAs' 
GEMINI_MODEL = 'gemini-flash-latest' # Đã update lên bản Flash mới nhất
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2-vision"

# --- SYSTEM PROMPT ĐỘNG (DYNAMIC) ---
def get_dynamic_prompt():
    # Lấy thông tin ngữ cảnh từ shared_state
    context_info = shared_state.get_system_prompt_context()
    
    base_prompt = f"""
    Bạn là một trợ lý Toán học và Khoa học chuyên nghiệp (Vision Expert).
    
    {context_info}

    QUY TẮC QUAN TRỌNG:
    1. Luôn trả lời bằng Tiếng Việt.
    2. Dùng LaTeX cho công thức: $...$ (inline), $$...$$ (block).
    3. Trình bày ngắn gọn, từng bước (Step-by-step).
    4. Bôi đậm kết quả cuối cùng.
    5. Chỉ show phần bài làm only. NO BULLSHIT.
    6. Nếu ảnh là code, hãy giải thích code hoặc viết lại code tối ưu hơn.
    
Môn học về CEA201x_1.1_VN Tổ chức và kiến trúc máy tính


    Trình bày được khái niệm máy tính, lịch sử phát triển, tổ chức và kiến trúc máy tính
    Hiểu được cách đánh giá hiệu suất máy tính
    Thực hiện được các phép toán luận lý trên bit: AND, OR, NOT, XOR, XNOR
    Biết cách biểu diễn hàm Boolean theo các cách: bảng chân trị, biểu thức đại số, mạch luận lý
    Thiết kế được mạch luận lý qua 3 bước: (1) Biểu diễn bảng chân trị, (2) Rút gọn luận lý, (3) Vẽ mạch luận lý
    Trình bày được tổ chức máy tính 3 thành phần theo mô hình Von-neumann
    Trình bày được tổ chức của bộ xử lý
    Trình bày được tổ chức của bộ nhớ chính và Hệ thống phân cấp bộ nhớ
    Trình bày được tổ chức của I/O và Bus
    Trình bày được các thành phần cơ bản của kiến trúc tập lệnh: lệnh, định dạng, toán hạng, mô hình định địa chỉ, biểu diễn lệnh và dữ liệu
    Hiểu được cách hoạt động của các lệnh số học và luận lý
    Hiểu được cách hoạt động của các lệnh truyền dữ liệu
    Hiểu được cách hoạt động của các lệnh điều khiển
    Biết cách chuyển từ hợp ngữ sang mã máy và ngược lại
    Biết cách sử dụng phần mềm mô phỏng phục vụ kiểm tra và gỡ lỗi chương trình
    Trình bày được các khái niệm cơ bản trong hợp ngữ, vai trò của macro, ký hiệu và nhãn trong chương trình hợp ngữ
    Viết được chương trình bằng hợp ngữ (lưu ý là chỉ sử dụng tập lệnh beta và bsim)
    Trình bày được tổ chức hỗ trợ song song mức lệnh
    Trình bày được tổ chức hỗ trợ song song mức dữ liệu và luồng
    """
    return base_prompt

# ===================== GIAO DIỆN ĐIỆN THOẠI (HTML) =====================
# (Giữ nguyên giao diện cũ vì đã hoạt động tốt)
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
                <span class="title">🤖 Vision AI (PC Master)</span>
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
        # Reset luôn trong shared state
        shared_state.save_state({"last_vision_content": "", "mode": "ready"})

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

            # --- LẤY DYNAMIC SYSTEM PROMPT ---
            current_system_prompt = get_dynamic_prompt()

            # --- OLLAMA STREAMING ---
            if engine == 'ollama':
                payload = { "model": OLLAMA_MODEL, "prompt": current_system_prompt+"\nGiải bài:", "images": [img_base64], "stream": True }
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
                
                # Payload Gemini mới với System Instruction
                user_msg = {"role": "user", "parts": [{"text": "Giải quyết vấn đề này:"}, {"inline_data": {"mime_type": "image/jpeg", "data": img_base64}}]}
                
                payload = { 
                    "system_instruction": {"parts": [{"text": current_system_prompt}]}, 
                    "contents": self.history + [user_msg], 
                    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4096} 
                }
                
                response = requests.post(url, json=payload, timeout=20)
                if response.status_code == 200:
                    try:
                        full_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                        # Giả lập stream vì requests không hỗ trợ stream response của Gemini dễ dàng
                        chunk_size = 15
                        for i in range(0, len(full_text), chunk_size):
                            chunk = full_text[i:i+chunk_size]
                            if self.window: self.window.evaluate_js(f"streamChunk({json.dumps(chunk)})")
                            self.server.emit_chunk(chunk)
                            time.sleep(0.005) # Delay cực nhẹ
                    except:
                        full_text = "Không nhận diện được nội dung trong ảnh."
                else: 
                    full_text = f"Lỗi API Gemini: {response.status_code} - {response.text}"

            if full_text:
                self.history.append({"role": "user", "parts": [{"text": "..."}]})
                self.history.append({"role": "model", "parts": [{"text": full_text}]})
                if len(self.history) > 6: self.history = self.history[-6:]
                
                # [QUAN TRỌNG] LƯU KẾT QUẢ VÀO SHARED STATE ĐỂ AUDIO ASSISTANT BIẾT
                shared_state.save_state({
                    "last_vision_content": full_text[:800], # Lưu 800 ký tự đầu để tiết kiệm token
                    "current_topic": "Vừa giải bài tập Vision",
                    "mode": "solving"
                })

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
    
    print(f"🚀 Vision AI (PC & Mobile) Started! Model: {GEMINI_MODEL}")
    
    # 3. Chạy GUI
    app.window = webview.create_window('Vision AI Pro Ecosystem', html=PC_HTML, width=480, height=650, on_top=True, js_api=app)
    webview.start()