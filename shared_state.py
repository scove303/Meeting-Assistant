import json
import os
import time

STATE_FILE = "session_context.json"

DEFAULT_STATE = {
    "subject": "CEA201x_1.1_VN Tổ chức và kiến trúc máy tính",
    "current_topic": "Tổng quan",
    "last_vision_content": "", # Nội dung từ màn hình vừa chụp
    "last_audio_content": "",  # Nội dung vừa nói
    "mode": "learning" # learning, coding, solving
}

def init_state():
    if not os.path.exists(STATE_FILE):
        save_state(DEFAULT_STATE)

def load_state():
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return DEFAULT_STATE

def save_state(new_data):
    try:
        current = load_state()
        current.update(new_data)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(current, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving state: {e}")

def get_system_prompt_context():
    state = load_state()
    return f"""
    --- THÔNG TIN NGỮ CẢNH HIỆN TẠI (SHARED CONTEXT) ---
    Môn học: {state.get('subject')}
    Chủ đề đang học: {state.get('current_topic')}
    Nội dung hình ảnh gần nhất: {state.get('last_vision_content')[:200]}...
    """