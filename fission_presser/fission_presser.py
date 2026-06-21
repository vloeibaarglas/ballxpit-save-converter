"""
BALL x Pit - Background Image Monitor & Clicker
Stage 1: Find & click fission card
Stage 2: After fission disappears, find & click "Whoa" button
"""

import sys
import time
import ctypes
import ctypes.wintypes
import numpy as np
import cv2

# ── Win32 API constants ──────────────────────────────────────────────
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
SW_RESTORE = 9

user32 = ctypes.windll.user32

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("_input", _INPUT),
    ]

def send_click(x: int, y: int):
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)
    abs_x = int(x * 65535 / screen_w)
    abs_y = int(y * 65535 / screen_h)
    inputs = (INPUT * 3)()
    inputs[0].type = INPUT_MOUSE
    inputs[0].mi.dx = abs_x
    inputs[0].mi.dy = abs_y
    inputs[0].mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
    inputs[1].type = INPUT_MOUSE
    inputs[1].mi.dwFlags = MOUSEEVENTF_LEFTDOWN
    inputs[2].type = INPUT_MOUSE
    inputs[2].mi.dwFlags = MOUSEEVENTF_LEFTUP
    user32.SendInput(3, ctypes.byref(inputs), ctypes.sizeof(INPUT))

# ── Config ───────────────────────────────────────────────────────────
WINDOW_TITLE = "BALL x Pit"
MATCH_THRESHOLD = 0.80
POLL_INTERVAL = 5.0
CLICK_DELAY = 0.3
Y_OFFSET = 200  # game renders with internal offset (see debug output)
# ─────────────────────────────────────────────────────────────────────

STAGES = [
    {"template": "fission.png", "name": "Fission card"},
    {"template": "whoa.png",    "name": "Whoa button"},
]

def find_window(title: str) -> int:
    hwnd = user32.FindWindowW(None, None)
    while hwnd:
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buf = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buf, length)
        if title.lower() in buf.value.lower():
            return hwnd
        hwnd = user32.GetWindow(hwnd, 2)
    return 0

def get_window_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom

def capture_window(hwnd: int) -> np.ndarray | None:
    left, top, right, bottom = get_window_rect(hwnd)
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return None
    hwndDC = user32.GetWindowDC(hwnd)
    if not hwndDC:
        return None
    mfcDC = ctypes.windll.gdi32.CreateCompatibleDC(hwndDC)
    saveBitMap = ctypes.windll.gdi32.CreateCompatibleBitmap(hwndDC, width, height)
    oldBmp = ctypes.windll.gdi32.SelectObject(mfcDC, saveBitMap)
    ctypes.windll.user32.PrintWindow(hwnd, mfcDC, 2)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.wintypes.DWORD),
            ("biWidth", ctypes.c_long),
            ("biHeight", ctypes.c_long),
            ("biPlanes", ctypes.wintypes.WORD),
            ("biBitCount", ctypes.wintypes.WORD),
            ("biCompression", ctypes.wintypes.DWORD),
            ("biSizeImage", ctypes.wintypes.DWORD),
            ("biXPelsPerMeter", ctypes.c_long),
            ("biYPelsPerMeter", ctypes.c_long),
            ("biClrUsed", ctypes.wintypes.DWORD),
            ("biClrImportant", ctypes.wintypes.DWORD),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    buf = ctypes.create_string_buffer(width * height * 4)
    ctypes.windll.gdi32.GetDIBits(mfcDC, saveBitMap, 0, height, buf, ctypes.byref(bmi), 0)
    ctypes.windll.gdi32.SelectObject(mfcDC, oldBmp)
    ctypes.windll.gdi32.DeleteObject(saveBitMap)
    ctypes.windll.gdi32.DeleteDC(mfcDC)
    user32.ReleaseDC(hwnd, hwndDC)
    img = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 4))
    return img

def click_at(hwnd: int, x: int, y: int):
    fg_hwnd = user32.GetForegroundWindow()
    client_pt = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(client_pt))
    screen_x = client_pt.x + x
    screen_y = client_pt.y + y + Y_OFFSET
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.05)
    send_click(screen_x, screen_y)
    time.sleep(0.05)
    if fg_hwnd and fg_hwnd != hwnd:
        user32.SetForegroundWindow(fg_hwnd)

def find_template(haystack: np.ndarray, needle: np.ndarray, threshold: float):
    result = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        h, w = needle.shape[:2]
        cx = max_loc[0] + w // 2
        cy = max_loc[1] + h // 2
        return cx, cy, max_val
    return None

def main():
    templates = []
    for stage in STAGES:
        img = cv2.imread(stage["template"], cv2.IMREAD_COLOR)
        if img is None:
            print(f"[ERROR] Cannot load {stage['template']}")
            sys.exit(1)
        templates.append(img)
        print(f"[OK] Loaded {stage['template']} ({img.shape[1]}x{img.shape[0]})")

    print(f"[OK] Stages: {' -> '.join(s['name'] for s in STAGES)}")
    print(f"[OK] Poll interval: {POLL_INTERVAL}s")
    print()

    while True:
        stage_idx = 0
        miss_count = 0

        while stage_idx < len(STAGES):
            stage = STAGES[stage_idx]
            needle = templates[stage_idx]

            hwnd = find_window(WINDOW_TITLE)
            if not hwnd:
                print(f"[WAIT] Window not found, retrying...")
                time.sleep(POLL_INTERVAL)
                continue

            frame = capture_window(hwnd)
            if frame is None:
                print("[WARN] Failed to capture window")
                time.sleep(POLL_INTERVAL)
                continue

            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            match = find_template(frame_bgr, needle, MATCH_THRESHOLD)

            if match:
                cx, cy, conf = match
                miss_count = 0
                print(f"[HIT] Stage {stage_idx+1} ({stage['name']}): ({cx}, {cy}) conf={conf:.3f}")
                click_at(hwnd, cx, cy)
                print(f"[CLICK] Sent click")
                if stage_idx < len(STAGES) - 1:
                    time.sleep(1.0)
                else:
                    time.sleep(CLICK_DELAY)
            else:
                miss_count += 1
                print(f"[MISS] Stage {stage_idx+1} ({stage['name']}): not found (miss #{miss_count})")

                if stage_idx < len(STAGES) - 1 and miss_count >= 2:
                    stage_idx += 1
                    miss_count = 0
                    print(f"\n>>> Advancing to stage {stage_idx+1}: {STAGES[stage_idx]['name']}\n")
                    time.sleep(1.0)
                    continue
                elif stage_idx == len(STAGES) - 1 and miss_count >= 2:
                    print("[DONE] Whoa button gone — restarting cycle.\n")
                    break

            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
