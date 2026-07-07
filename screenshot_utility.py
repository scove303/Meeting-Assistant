import keyboard
import mouse
import os
import time
from PIL import ImageGrab
from datetime import datetime

# --- CẤU HÌNH ---
HOTKEY = 'ctrl+shift+alt+z' # Tổ hợp phím bạn muốn
SAVE_PATH = "screenshots"
QUALITY = 100  # Chất lượng ảnh tối thiểu để tối ưu dung lượng
SHOW_PREVIEW = False # Toggle hiển thị ảnh sau khi chụp

if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

def take_screenshot(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    
    # Tính toán vùng chọn
    left, top = min(x1, x2), min(y1, y2)
    right, bottom = max(x1, x2), max(y1, y2)
    
    width = right - left
    height = bottom - top

    if width < 5 or height < 5:
        print("❌ Vùng chọn quá nhỏ, không chụp.")
        return

    try:
        # Chụp màn hình (tuyệt đối không hiện thông báo hệ thống)
        img = ImageGrab.grab(bbox=(left, top, right, bottom))
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_PATH, f"snap_{timestamp}.jpg")
        
        # Lưu với chất lượng cực thấp để giảm dung lượng
        img.save(filename, "JPEG", quality=QUALITY, optimize=True)
        print(f"✅ Đã lưu: {filename} ({width}x{height})")
        
        if SHOW_PREVIEW:
            os.startfile(filename)
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def main():
    print(f"--- CHƯƠNG TRÌNH ĐANG CHẠY (ADMIN) ---")
    print(f"Tổ hợp phím: {HOTKEY}")
    print("Nhấn ESC để thoát hoàn toàn.")
    print("---------------------------------------")

    while True:
        try:
            # 1. Chờ cho đến khi tổ hợp phím được nhấn giữ
            if keyboard.is_pressed(HOTKEY):
                start_pos = mouse.get_position()
                print(f"🟢 Đang ghi... Bắt đầu tại: {start_pos}")
                
                # 2. Vòng lặp chờ cho đến khi NHẢ tổ hợp phím
                # Trong lúc này, chúng ta in ra tọa độ hiện tại (Debug vẽ đường thẳng)
                while keyboard.is_pressed(HOTKEY):
                    current_pos = mouse.get_position()
                    # Log nhẹ để biết chương trình vẫn đang sống khi bạn kéo chuột
                    print(f"   [Kéo] Chuột đang ở: {current_pos}", end='\r')
                    time.sleep(0.05)
                
                # 3. Khi đã nhả phím
                end_pos = mouse.get_position()
                print(f"\n🔴 Kết thúc tại: {end_pos}")
                
                take_screenshot(start_pos, end_pos)
            
            # Thoát chương trình
            if keyboard.is_pressed('esc'):
                print("Đang thoát...")
                break
                
            time.sleep(0.01) # Giảm tải CPU
            
        except Exception as e:
            print(f"Lỗi vòng lặp: {e}")
            time.sleep(1)

if __name__ == "__main__":
    # Kiểm tra xem có phải Admin không để cảnh báo
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("⚠️ CẢNH BÁO: CHƯA CHẠY QUYỀN ADMIN. CÓ THỂ KHÔNG NHẬN PHÍM.")
    
    main()