import ctypes
from ctypes import wintypes

running = False
saved_mouse_pos = None

_job = None
_root = None

_generation = 0


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG),
                ("y", wintypes.LONG)]


def get_mouse_pos():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def _cancel_job():
    global _job, _root
    if _job is not None and _root is not None:
        try:
            _root.after_cancel(_job)
        except Exception:
            pass
    _job = None
    _root = None


def start():
    global running
    running = True


def is_running():
    return running


def stop():
    global running, saved_mouse_pos, _generation
    running = False
    saved_mouse_pos = None

    _generation += 1

    _cancel_job()


def click(x, y):
    ctypes.windll.user32.SetCursorPos(x, y)
    ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)  # down
    ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)  # up


def arm(root, ClickX1, ClickY1, ClickX2, ClickY2, intervaltime, delay_ms=0):
    global running, _root, _job, _generation

    running = True
    _generation += 1
    gen = _generation

    _root = root
    _cancel_job()

    _job = root.after(
        int(delay_ms),
        autoclick,
        gen, root, ClickX1, ClickY1, ClickX2, ClickY2, intervaltime
    )


def autoclick(gen, root, ClickX1, ClickY1, ClickX2, ClickY2, intervaltime):
    global running, saved_mouse_pos, _job, _root, _generation

    if gen != _generation:
        return

    _root = root
    _job = None

    if not running:
        return

    X1 = int(ClickX1.get())
    Y1 = int(ClickY1.get())
    X2 = int(ClickX2.get())
    Y2 = int(ClickY2.get())

    try:
        refresh_sec = int(intervaltime.get())
    except Exception:
        refresh_sec = 60

    saved_mouse_pos = get_mouse_pos()

    if not (X1 == 0 and Y1 == 0):
        click(X1, Y1)

    if not (X2 == 0 and Y2 == 0):
        click(X2, Y2)

    if saved_mouse_pos:
        x0, y0 = saved_mouse_pos
        ctypes.windll.user32.SetCursorPos(x0, y0)

    if not running or gen != _generation:
        return

    _job = root.after(
        refresh_sec * 1000,
        autoclick,
        gen, root, ClickX1, ClickY1, ClickX2, ClickY2, intervaltime
    )
