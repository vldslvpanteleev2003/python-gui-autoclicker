import time
import ctypes
from ctypes import wintypes

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG),
                ("y", wintypes.LONG)]

def get_mouse_pos(Coordinates, root):
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    Coordinates.config(text=f"X={pt.x}, Y={pt.y}")
    root.after(100, get_mouse_pos, Coordinates, root)