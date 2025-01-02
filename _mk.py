import time
import random
import math
import win32con

import ctypes
from ctypes import Structure, c_long, c_ulong, sizeof, POINTER, pointer, byref, c_ushort

# yes this uses SendInput from Windows API that emulates mouse / keyboard inputs
# i couldnt get this to work with other frameworks i know of so this is a temporary solution
# ty chatgpt :skull:

# constants
INPUT_MOUSE              =   0
MOUSEEVENTF_MOVE         =   0x0001
MOUSEEVENTF_VIRTUALDESK  =   0x4000
MOUSEEVENTF_ABSOLUTE     =   0x8000
MOUSEEVENTF_LEFTDOWN     =   0x0002
MOUSEEVENTF_LEFTUP       =   0x0004
MOUSEEVENTF_WHEEL        =   0x0800

INPUT_KEYBOARD           =   1
KEYEVENTF_KEYUP          =   0x0002
KEYEVENTF_UNICODE        =   0x0004
KEYEVENTF_SCANCODE       =   0x0008

SM_CXSCREEN              =   0
SM_CYSCREEN              =   1

# input structures rahhhhhhh
class MOUSEINPUT(Structure):
    _fields_ = [
        ("dx", c_long),
        ("dy", c_long),
        ("mouseData", c_ulong),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", POINTER(c_ulong))
    ]

class KEYBDINPUT(Structure):
    _fields_ = [
        ("wVk", c_ushort),
        ("wScan", c_ushort),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", POINTER(c_ulong))
    ]

class _INPUTunion(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT)
    ]

class INPUT(Structure):
    _fields_ = [
        ("type", c_ulong),
        ("union", _INPUTunion)
    ]

# keyboard input emulation
class Keyboard:
    def __init__(self):
        self.user32 = ctypes.windll.user32

        # add misc key mappings, will extend later
        self.key_mapping = {
            'shift': win32con.VK_SHIFT,
            'ctrl': win32con.VK_CONTROL,
            'alt': win32con.VK_MENU,
            'enter': win32con.VK_RETURN,
            'space': win32con.VK_SPACE,
            'tab': win32con.VK_TAB,
            'backspace': win32con.VK_BACK,
            'delete': win32con.VK_DELETE,
            'escape': win32con.VK_ESCAPE,
            'up': win32con.VK_UP,
            'down': win32con.VK_DOWN,
            'left': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT,
        }

        # add number keys
        for i in range(10):
            self.key_mapping[str(i)] = ord(str(i))

        # add letter keys
        for c in 'abcdefghijklmnopqrstuvwxyz':
            self.key_mapping[c] = ord(c.upper())

    # create keyboard input structure
    def _create_keyboard_input(self, key, key_up=False):
        inp = INPUT()
        inp.type = INPUT_KEYBOARD

        # single characters
        if isinstance(key, str) and len(key) == 1:
            vk_code = ord(key.upper())

        # special keys
        elif isinstance(key, str) and key.lower() in self.key_mapping:
            vk_code = self.key_mapping[key.lower()]

        # misc keys
        else:
            vk_code = key

        # get scan code from virtual key code
        scan_code = self.user32.MapVirtualKeyW(vk_code, 0)

        inp.union.ki.wVk = vk_code
        inp.union.ki.wScan = scan_code
        inp.union.ki.dwFlags = KEYEVENTF_KEYUP if key_up else 0
        inp.union.ki.time = 0
        inp.union.ki.dwExtraInfo = pointer(c_ulong(0))

        return inp

    # simple keypress
    def press(self, key, hold=70):

        # key down
        inp = self._create_keyboard_input(key)
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))

        # hold
        hold = hold/1000
        hold_time = random.uniform(hold - (hold * 0.1), hold + (hold * 0.1))
        time.sleep(hold_time)
        
        # key up
        inp = self._create_keyboard_input(key, key_up=True)
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))

    # hold down key
    def hold(self, key):
        inp = self._create_keyboard_input(key)
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))

    # release the key
    def release(self, key):
        inp = self._create_keyboard_input(key, key_up=True)
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))

    # combination of two or more keys
    def combo(self, keys, hold=1000):

        # press keys
        for key in keys:
            self.hold(key)
            time.sleep(random.uniform(0.01, 0.02))

        # hold
        hold = hold/1000
        hold_time = random.uniform(hold - (hold * 0.1), hold + (hold * 0.1))
        time.sleep(hold_time)

        # release keys
        for key in reversed(keys):
            self.release(key)
            time.sleep(random.uniform(0.01, 0.02))

class Mouse:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        # get actual screen metrics stuff
        self.screen_width = self.user32.GetSystemMetrics(SM_CXSCREEN)
        self.screen_height = self.user32.GetSystemMetrics(SM_CYSCREEN)

    # get current primary monitor absolute coords
    def _abs_coords(self, x, y):

        # windows expects coordinates in range 0-65535
        x = max(0, min(x, self.screen_width))
        y = max(0, min(y, self.screen_height))

        # scale the coordinates
        scaled_x = int((x * 65535) / self.screen_width)
        scaled_y = int((y * 65535) / self.screen_height)

        # make sure to not exceed min/max values
        return (min(65535, scaled_x), min(65535, scaled_y))

    # add some randomness to control points for more natural movement
    def _gen_human_curve(self, start_x, start_y, end_x, end_y, steps):
        control_x = random.uniform(min(start_x, end_x), max(start_x, end_x))
        control_y = random.uniform(min(start_y, end_y), max(start_y, end_y))

        points = []
        for i in range(steps + 1):
            t = i / steps
            t = self._ease_in_out(t)

            # calculate bezier curve points... yes thats right
            x = (1 - t)**2 * start_x + 2 * (1 - t) * t * control_x + t**2 * end_x
            y = (1 - t)**2 * start_y + 2 * (1 - t) * t * control_y + t**2 * end_y

            points.append((int(x), int(y)))
        return points

    # smoother easing thing
    def _ease_in_out(self, t):
        if t < 0.5:
            return 2 * t * t
        return -1 + (4 - 2 * t) * t

    # move the cursor to screen coordinates
    # kms
    def move(self, x, y, duration=500):

        # get current position
        class POINT(Structure):
            _fields_ = [("x", c_long), ("y", c_long)]
        pt = POINT()
        self.user32.GetCursorPos(byref(pt))
        start_x, start_y = pt.x, pt.y

        # calculate distance, adjust steps
        distance = math.sqrt((x - start_x)**2 + (y - start_y)**2)
        steps = max(10, min(50, int(distance / 10)))

        # generate movement curve
        points = self._gen_human_curve(start_x, start_y, x, y, steps)

        # prepare input structure
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.mouseData = 0
        inp.union.mi.time = 0
        inp.union.mi.dwExtraInfo = pointer(c_ulong(0))

        # move through points
        step_delay = duration / (steps * 1000)  # Convert to seconds

        for point_x, point_y in points:
            # convert to absolute coordinates
            abs_x, abs_y = self._abs_coords(point_x, point_y)

            # set up movement
            inp.union.mi.dx = abs_x
            inp.union.mi.dy = abs_y
            inp.union.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE

            # send movement
            self.user32.SendInput(1, byref(inp), sizeof(INPUT))

            # add small random delay, temoorary
            time.sleep(random.uniform(step_delay * 0.8, step_delay * 1.2))

    # click...
    def click(self, hold=60):
        inp = INPUT()
        inp.type = INPUT_MOUSE

        # mouse down
        inp.union.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))

        # hold
        hold = hold/1000
        hold_time = random.uniform(hold - (hold * 0.1), hold + (hold * 0.1))
        time.sleep(hold_time)

        # mouse up
        inp.union.mi.dwFlags = MOUSEEVENTF_LEFTUP
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))

    # scroll stuff
    def scroll(self, delta):
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.mouseData = int(delta)
        inp.union.mi.dwFlags = MOUSEEVENTF_WHEEL
        self.user32.SendInput(1, byref(inp), sizeof(INPUT))
