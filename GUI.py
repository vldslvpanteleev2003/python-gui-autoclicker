import tkinter as tk
from tkinter import messagebox
import configparser
import os
import ctypes
from checkpixel import get_mouse_pos
import autoclicker as ac
import threading
from ctypes import wintypes

CONFIG_FILE = "config.ini"
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
WM_APP = 0x8000
WM_SET_HOTKEY = WM_APP + 1

HOTKEY_ID = 1
hotkey_thread_id = None
hotkey_vk = None

VK_LBUTTON = 0x01
mouse_watch_job = None
_lbutton_prev_down = False

GetCursorPos = ctypes.windll.user32.GetCursorPos
SetCursorPos = ctypes.windll.user32.SetCursorPos
GetPixel = ctypes.windll.gdi32.GetPixel
GetDC = ctypes.windll.user32.GetDC
mouse_event = ctypes.windll.user32.mouse_event

def on_close():
    if hotkey_thread_id:
        user32.PostThreadMessageW(hotkey_thread_id, WM_QUIT, 0, 0)
    root.destroy()

def set_hotkey(event):
    vk = keysym_to_vk(event)

    if not hotkey_thread_id:
        messagebox.showerror("Hotkey", "The thread isn't ready yet")
        root.unbind_all("<Key>")
        return

    ok = user32.PostThreadMessageW(hotkey_thread_id, WM_SET_HOTKEY, vk, 0)
    if not ok:
        err = ctypes.get_last_error()
        messagebox.showerror("Hotkey", f"Error: {err}")

    root.unbind_all("<Key>")

def keysym_to_vk(event):
    ks = event.keysym

    if ks.startswith("F") and ks[1:].isdigit():
        n = int(ks[1:])
        if 1 <= n <= 24:
            return 0x70 + (n - 1)

    if len(ks) == 1 and ks.isalpha():
        return ord(ks.upper())

    if len(ks) == 1 and ks.isdigit():
        return ord(ks)

    if ks == "Escape":
        return 0x1B

    return event.keycode

def autoclick_toggle():
    if ac.running:
        autoclickstop()
    else:
        autoclickstart()

def hotkey_thread_proc():
    global hotkey_thread_id, hotkey_vk

    hotkey_thread_id = kernel32.GetCurrentThreadId()

    msg = wintypes.MSG()
    user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)

    current_vk = None

    while True:
        ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
        if ret == 0:
            break

        if msg.message == WM_SET_HOTKEY:
            new_vk = int(msg.wParam)

            if current_vk is not None:
                user32.UnregisterHotKey(None, HOTKEY_ID)

            ok = user32.RegisterHotKey(None, HOTKEY_ID, MOD_NOREPEAT, new_vk)
            if not ok:
                err = ctypes.get_last_error()
                root.after(0, lambda e=err: messagebox.showerror("Hotkey", f"Failed to register hotkey: {e}"))
                current_vk = None
                hotkey_vk = None
            else:
                current_vk = new_vk
                hotkey_vk = new_vk
                root.after(0, lambda vk=new_vk: hotkey_label.config(text=f"Hotkey: VK {vk}"))

        elif msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
            root.after(0, autoclick_toggle)

    if current_vk is not None:
        user32.UnregisterHotKey(None, HOTKEY_ID)

def flush_mouse_state():
    global _lbutton_prev_down
    state = ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON)
    _lbutton_prev_down = bool(state & 0x8000)

def user_clicked_left_mouse():
    global _lbutton_prev_down
    state = ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON)
    down = bool(state & 0x8000)
    clicked = down and not _lbutton_prev_down
    _lbutton_prev_down = down
    return clicked

def set_status_running(is_running: bool):
    if is_running:
        status_label.config(text="Status: working", bg="green")
    else:
        status_label.config(text="Status: stopped", bg="red")

def mouse_watch():
    global mouse_watch_job

    if not ac.running:
        mouse_watch_job = None
        return

    if user_clicked_left_mouse() and stop_on_click.get():
        autoclickstop()
        return

    mouse_watch_job = root.after(15, mouse_watch)

def load_click_settings(ClickX1, ClickY1, ClickX2, ClickY2, intervaltime, stop_on_click):
    global hotkey_vk
    if not os.path.exists(CONFIG_FILE):
        return

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")

    if "clicker" not in config:
        return

    def safe_set(spinbox, value):
        spinbox.delete(0, "end")
        spinbox.insert(0, value)

    section = config["clicker"]

    try:
        safe_set(ClickX1, section.get("x1", "0"))
        safe_set(ClickY1, section.get("y1", "0"))
        safe_set(ClickX2, section.get("x2", "0"))
        safe_set(ClickY2, section.get("y2", "0"))
        safe_set(intervaltime, section.get("interval", "60"))
        stop_on_click.set(section.get("stop_on_click", "0") == "1")
    except Exception as e:
        print("Error to load config.ini:", e)

    hk = section.get("hotkey_vk")
    if hk is not None:
        try:
            hotkey_vk = int(hk)
            hotkey_label.config(text=f"Hotkey: VK {hotkey_vk}")

            if hotkey_thread_id:
                user32.PostThreadMessageW(
                    hotkey_thread_id,
                    WM_SET_HOTKEY,
                    hotkey_vk,
                    0
                )
        except ValueError:
            pass

def save_click_settings(x1, y1, x2, y2, interval, stop_on_click_value, hotkey_vk_value):
    config = configparser.ConfigParser()

    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE, encoding="utf-8")

    if "clicker" not in config:
        config["clicker"] = {}

    section = config["clicker"]
    section["x1"] = str(x1)
    section["y1"] = str(y1)
    section["x2"] = str(x2)
    section["y2"] = str(y2)
    section["interval"] = str(interval)
    section["stop_on_click"] = "1" if stop_on_click_value else "0"

    if hotkey_vk_value is not None:
        section["hotkey_vk"] = str(hotkey_vk_value)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)

def isint(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def checkinput():
    time = intervaltime.get()
    X1 = ClickX1.get()
    Y1 = ClickY1.get()
    X2 = ClickX2.get()
    Y2 = ClickY2.get()
    if time.isdigit() == False:
        return -1
    if (isint(X1) == False) or (isint(Y1) == False) or (isint(X2) == False) or (isint(Y2) == False):
        return -2
    else:
        time = int(time)
        if (time < 60) or (time > 540):
            return -1
        else:
            return 0


def autoclickstart():
    code = checkinput()
    if code == 0:
        if ac.running:
            autoclickstop()
        set_status_running(True)
        save_click_settings(
            ClickX1.get(), ClickY1.get(), ClickX2.get(), ClickY2.get(),
            intervaltime.get(), stop_on_click.get(), hotkey_vk
        )
        ac.arm(root, ClickX1, ClickY1, ClickX2, ClickY2, intervaltime, delay_ms=10000)
        flush_mouse_state()
        mouse_watch()

    elif code == -1:
        status_label.config(text="Status: stopped", bg="red")
        autoclickstop()
        messagebox.showinfo("Error", "Interval must be between 60 and 540 seconds. Only numbers are allowed.")
    elif code == -2:
        status_label.config(text="Status: stopped", bg="red")
        autoclickstop()
        messagebox.showinfo("Error", "Coordinates must contain only numbers.")

def autoclickstop():
    global mouse_watch_job
    ac.stop()
    set_status_running(False)
    if mouse_watch_job is not None:
        root.after_cancel(mouse_watch_job)
        mouse_watch_job = None

def set_value(spin):
    spin.delete(0, "end")
    spin.insert(0, "0")

def showpixel():
    get_mouse_pos(Coordinates, root)

root = tk.Tk()
root.title("AutoClicker")
root.resizable(False, False)
root.geometry("250x350")

hotkey_thread = threading.Thread(target=hotkey_thread_proc,daemon=True)
hotkey_thread.start()

Coordinates = tk.Label(root, text="")
Coordinates.pack()
showpixel()

status_label = tk.Label(root, text="Status: stopped", bg="red", fg="white")
status_label.pack(pady=5)

offset_var = tk.StringVar(value="0")
label1 = tk.Label(root, text="Coordinates X1 Y1:")
label1.pack()
ClickX1 = tk.Spinbox(root, from_=-5000, to=5000)
ClickX1.pack()
ClickY1 = tk.Spinbox(root, from_=-5000, to=5000)
ClickY1.pack()
set_value(ClickX1)
set_value(ClickY1)

label2 = tk.Label(root, text="Coordinates X2 Y2:")
label2.pack()
ClickX2 = tk.Spinbox(root, from_=-5000, to=5000)
ClickX2.pack()
ClickY2 = tk.Spinbox(root, from_=-5000, to=5000)
ClickY2.pack()
set_value(ClickX2)
set_value(ClickY2)

interval = tk.Label(root, text="Click interval (seconds):")
interval.pack()

intervaltime = tk.Spinbox(root, from_=60, to=540)
intervaltime.pack()

stop_on_click = tk.BooleanVar(value=False)
stop_on_click_checkbox = tk.Checkbutton(root,text="Stop on mouse click", variable=stop_on_click)
stop_on_click_checkbox.pack(pady=5)

hotkey_label = tk.Label(root, text="Hotkey: empty")
hotkey_label.pack()

hotkey_button = tk.Button(root,text="Bind hotkey",command=lambda: root.bind_all("<Key>", set_hotkey))
hotkey_button.pack()

load_click_settings(ClickX1, ClickY1, ClickX2, ClickY2, intervaltime, stop_on_click)

start_button = tk.Button(root, text="Start", command=autoclickstart)
start_button.pack()

stop_button = tk.Button(root, text="Stop", command=autoclickstop)
stop_button.pack()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
