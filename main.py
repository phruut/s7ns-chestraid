import dearpygui.dearpygui as dpg
import time
import win32gui
import win32con
import threading
import sys
from datetime import datetime, timedelta, timezone
from _mk import Mouse, Keyboard


# window things
# -----------------------------------------

# for selecting target window
def wait_target_win():
    global HWND
    dpg.set_value('status_text', 'select')

    # wait for user
    while HWND is None and RUNNING:
        dpg.set_value('status_text_hover', f'click the {WINTITLE} window')
        time.sleep(0.1)

        active_hwnd = win32gui.GetForegroundWindow()
        if win32gui.GetWindowText(active_hwnd) == WINTITLE:
            HWND = active_hwnd
            break
    
    # after selects
    if HWND and win32gui.IsWindow(HWND):
        dpg.set_value('status_text', 'selected')
        dpg.set_value('status_text_hover', f'target: {HWND}')

        rect = win32gui.GetWindowRect(HWND)
        x = rect[0]
        y = rect[1]

        win32gui.SetWindowPos(HWND, None, x, y, WIDTH, HEIGHT, win32con.SWP_SHOWWINDOW)
        return True
    return False

def activate_window():
    if HWND and win32gui.IsWindow(HWND):
        win32gui.SetForegroundWindow(HWND)
        time.sleep(0.5)



# time things
# -----------------------------------------

# seconds until next interval
def interval(now, interval_minutes):
    next_time = (now + timedelta(minutes=interval_minutes - (now.minute % interval_minutes))).replace(second=0, microsecond=0)
    return (next_time - now).total_seconds()

# utc time..
def get_utc():
    return datetime.now(timezone.utc)

# gets the next raid time based on utc
def get_next_raid(utc, interval_seconds=7200, start_second=0):

    # calculate total seconds since 0:00
    current_seconds = utc.hour * 3600 + utc.minute * 60 + utc.second

    # adjust time since start to calculate the next raid time
    time_since_start = (current_seconds - start_second) % interval_seconds

    # if exactly on a raid time, the next raid is just the next interval
    if time_since_start == 0:
        next_seconds = current_seconds
    else:
        next_seconds = current_seconds + (interval_seconds - time_since_start)

    # convert next_seconds to day rollover safe time
    next_raid = utc.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=next_seconds)

    # IM SO FUCKING COOKED HOLY SHIT im so sleepy
    return next_raid

# raid end time
def get_raid_end(raid_start_time, seconds=800):
    raid_end = raid_start_time + timedelta(seconds=seconds)
    return raid_end



# relative cursor move
# -----------------------------------------

# get the target window pos for relative mouse inputs
def get_window_rect():
    if HWND and win32gui.IsWindow(HWND):
        rect = win32gui.GetClientRect(HWND)
        point = win32gui.ClientToScreen(HWND, (0, 0))
        return {
            'left': point[0],
            'top': point[1],
            'width': rect[2],
            'height': rect[3]
        }

# move mouse relative to the target window coordinates
def moverel(x, y):
    rect = get_window_rect()
    if rect:
        screen_x = rect['left'] + x
        screen_y = rect['top'] + y
        mouse.move(screen_x, screen_y)



# automation things 
# temporary and will be worked on with proper gui for future scripts
# -----------------------------------------

# before raid
# afk the final event zone 11 while waiting for next raid
def pre_act():
    activate_window()
    dpg.set_value('status_text', 'prep...')

    # move to x on raid result
    time.sleep(3)
    dpg.set_value('status_text', 'move x')
    moverel(745,110)

    # click
    time.sleep(0.3)
    dpg.set_value('status_text', 'click')
    mouse.click()

    # move cursor to tp
    time.sleep(0.3)
    dpg.set_value('status_text', 'move tp')
    moverel(105, 185)

    # click the icon
    time.sleep(0.3)
    dpg.set_value('status_text', 'click')
    mouse.click()

    # scroll down
    time.sleep(0.3)
    dpg.set_value('status_text', 'scroll')
    mouse.scroll(-1000)

    # move to final zone
    time.sleep(0.3)
    dpg.set_value('status_text', 'move 11')
    moverel(485,360)

    # click final zone
    time.sleep(0.3)
    dpg.set_value('status_text', 'click')
    mouse.click()

    # cannon wait
    time.sleep(1)
    dpg.set_value('status_text', 'wait')
    time.sleep(9)

    # hoverboard
    dpg.set_value('status_text', 'hover')
    keyboard.press('q')

    # move to middle of final zone
    time.sleep(0.5)
    dpg.set_value('status_text', 'zone')
    keyboard.combo(['w','d'], 450)

# moves the player into the raid portal :D
def raid_act():
    time.sleep(15)
    activate_window() 
    time.sleep(1)
    dpg.set_value('status_text', 'moving')
    keyboard.combo(['s','d'], 900)

# anti-afk thing
def afk_act():
    activate_window()
    time.sleep(1)
    dpg.set_value('status_text', 'jump!')
    keyboard.press('space')

# automation thread
def automation_thread():
    global RUNNING, HWND

    # if the target window is gone...
    if not wait_target_win():
        dpg.set_value('status_text', 'failed')
        dpg.set_value('status_text_hover', 'couldnt find target window')
        RUNNING = False
        HWND = None
        return

    try:
        pre_act()
        last_anti_afk_minute = None
        next_raid_time = get_next_raid(get_utc())
        in_raid = False

        while RUNNING:

            # fetch time stiuff
            utc = get_utc()
            raid_end_time = get_raid_end(next_raid_time)

            # in raid
            if utc >= next_raid_time and utc < raid_end_time and not in_raid:
                raid_act()
                in_raid = True

            # raid ends
            elif utc >= raid_end_time and in_raid:
                pre_act()
                in_raid = False
                next_raid_time = get_next_raid(utc)  # calculate next raid after current ends

            # if anti-afk is on it will do this
            if dpg.get_value('anti_afk') and utc.minute % 10 == 0 and last_anti_afk_minute != utc.minute:
                afk_act()
                last_anti_afk_minute = utc.minute

            update_status()
            time.sleep(0.2)

    except Exception as e:
        print(f'automation thread: {e}')
    finally:
        RUNNING = False
        if dpg.is_dearpygui_running():
            dpg.configure_item('run_button', label='START')
            update_status()



# gui things
# -----------------------------------------

# status text updating yep
def update_status():
    if not dpg.is_dearpygui_running():
        return

    # aaaaa
    utc = get_utc()
    next_raid = get_next_raid(utc) 

    # running status
    if not RUNNING:
        status_text = 'inactive'
        tooltip_text = 'waiting for start...'

    # this part updates the hover text thing
    else:
        status_text = 'waiting'
        remaining_time = next_raid - utc
        total_seconds = int(remaining_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            countdown = f'{hours}h {minutes}m {seconds}s'
        elif minutes > 0:
            countdown = f'{minutes}m {seconds}s' 
        else:
            countdown = f'{seconds}s'
        tooltip_text = f'next raid: {countdown}'

    # do this cuz idk
    try:
        dpg.set_value('status_text', status_text)
        dpg.set_value('status_text_hover', tooltip_text)
    except SystemError:
        pass

# always on top
def aot_callback():
    dpg.set_viewport_always_top(dpg.get_value('always_on_top'))

# main thing
def run_callback():
    global RUNNING, automation_thread_handle

    if not RUNNING:
        RUNNING = True
        automation_thread_handle = threading.Thread(target=automation_thread)
        automation_thread_handle.daemon = True
        automation_thread_handle.start()
        dpg.configure_item('run_button', label='STOP')
    else:
        RUNNING = False
        dpg.configure_item('run_button', label='START')

# make gui, look at this indenting :sob: wtf
def create_gui():
    dpg.create_context()
    with dpg.window(tag='main'):
         with dpg.tab_bar():
            with dpg.tab(label='main'):
                dpg.add_spacer(height=0.5)
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_checkbox(label='anti-afk', tag='anti_afk', default_value=True)
                        with dpg.tooltip(dpg.last_item()):
                            dpg.add_text('jumps every 10 minutes')
                        dpg.add_checkbox(label='always on top', tag='always_on_top', default_value=True, callback=aot_callback)
                        with dpg.tooltip(dpg.last_item()):
                            dpg.add_text('makes this window stay on top')

                        #dpg.add_checkbox(label='disable rmb', tag='disable_rmb', default_value=True, callback=rmb_callback)
                        #with dpg.tooltip(dpg.last_item()):
                        #    dpg.add_text('no right click to avoid accidentally moving the camera angle', wrap=240)
                        dpg.add_text('...')

                        dpg.add_spacer(height=2)
                        with dpg.group(horizontal=True):
                            dpg.add_text('status:')
                            dpg.add_text('inactive', color=(100, 149, 238), tag='status_text')
                            with dpg.tooltip(dpg.last_item()):
                                dpg.add_text('waiting for start...', tag='status_text_hover')
                    dpg.add_spacer(width=17)
                    with dpg.group():
                        dpg.add_button(label='START', tag='run_button', width=91, height=91, callback=run_callback)

            with dpg.tab(label='instructions'):
                dpg.add_spacer(height=0.5)
                dpg.add_text('join raid team private server', bullet=True)
                dpg.add_text('enter the event world', bullet=True)
                with dpg.group(horizontal=True):
                    dpg.add_text('click', bullet=True)
                    dpg.add_text('START')
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text("on 'main' tab")
                    dpg.add_text('button')
                dpg.add_text('click roblox window and wait', bullet=True)



# run main
# -----------------------------------------

if __name__ == '__main__':

    # global vars stuff
    RUNNING = False
    HWND = None
    WINTITLE = "Roblox"
    WIDTH = 1
    HEIGHT = 1

    mouse = Mouse()
    keyboard = Keyboard()

    # setup and start gui
    create_gui()
    dpg.create_viewport(title='S7NS ChestRaid', min_width=270, min_height=176, width=270, height=176, resizable=False)
    dpg.set_viewport_always_top(dpg.get_value('always_on_top'))
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window('main', True)
    dpg.start_dearpygui()
    dpg.destroy_context()
    sys.exit(0)