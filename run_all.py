import subprocess
import sys
import time

# Đường dẫn Python trong venv hiện tại
PYTHON_EXE = sys.executable

# Đường dẫn 2 file script bạn muốn chạy
SCRIPT_1 = "audio_assistant.py" # Thay tên file của bạn vào
SCRIPT_2 = "math_n_calculating_assistant_2.py" # Thay tên file của bạn vào

print(f"🚀 Đang khởi động {SCRIPT_1} và {SCRIPT_2}...")

try:
    # Chạy script 1
    p1 = subprocess.Popen([PYTHON_EXE, SCRIPT_1])
    
    # Đợi xíu cho script 1 ổn định (tùy chọn)
    time.sleep(2) 
    
    # Chạy script 2
    p2 = subprocess.Popen([PYTHON_EXE, SCRIPT_2])

    print("✅ Cả 2 đang chạy. Nhấn Ctrl+C để dừng tất cả.")
    
    # Giữ cho file tổng này sống để giám sát
    p1.wait()
    p2.wait()

except KeyboardInterrupt:
    print("\n🛑 Đang dừng tất cả...")
    p1.terminate()
    p2.terminate()
    sys.exit()