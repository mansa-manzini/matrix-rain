#!/usr/bin/env python3

import random
import curses
import time

# Sleep between frame after refresh so that user can see the frame. Value 0.01 or lower results in flickering because
# the animation is too fast.
SLEEP_BETWEEN_FRAME = .04  # about 25 frames/s is good enough

# How fast the rain should fall. In config, we change it according to screen.
FALLING_SPEED = 2

# The max number of falling rains. In config, we change it according to screen.
MAX_RAIN_COUNT = 10

# Color gradient for rain
COLOR_STEP = 20
NUMBER_OF_COLOR = 50  # The darkest color is 1000 - COLOR_STEP * NUMBER_OF_COLOR. This should be >= 0
USE_GRADIENT = False
START_COLOR_NUM = 128  # The starting number for color in gradient to avoid changing the first 16 basic colors

# Different styles for rain head
HEAD_STANDOUT = curses.COLOR_WHITE | curses.A_STANDOUT  # look better for small font
HEAD_BOLD = curses.COLOR_WHITE | curses.A_BOLD  # look better for larger font

# TODO This can be a namedtuple
options = {
    'head': HEAD_STANDOUT,
    'speed': FALLING_SPEED,
    'count': MAX_RAIN_COUNT,
}


# Reset the options value according to screen size
def config(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    init_colors()

    options['count'] = curses.COLS//2
    options['speed'] = 1 + curses.LINES//25


def init_colors():
    curses.start_color()
    global USE_GRADIENT
    USE_GRADIENT = curses.can_change_color()  # use xterm-256 if this is false

    if USE_GRADIENT:
        curses.init_color(curses.COLOR_WHITE, 1000, 1000, 1000)
        curses.init_color(curses.COLOR_BLACK, 0, 0, 0)  # make sure background is black
        for i in range(NUMBER_OF_COLOR + 1):
            green_value = (1000 - COLOR_STEP * NUMBER_OF_COLOR) + COLOR_STEP * i
            curses.init_color(START_COLOR_NUM + i, 0, green_value, 0)
            curses.init_pair(START_COLOR_NUM + i, START_COLOR_NUM + i, curses.COLOR_BLACK)
    else:
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)


def get_matrix_code_chars():
    l = [chr(i) for i in range(0x21, 0x7E)]
    # half-width katakana. See https://en.wikipedia.org/wiki/Halfwidth_and_fullwidth_forms
    l.extend([chr(i) for i in range(0xFF66, 0xFF9D)])
    return l


MATRIX_CODE_CHARS = get_matrix_code_chars()


def random_char():
    return random.choice(MATRIX_CODE_CHARS)


def random_rain_length():
    return random.randint(curses.LINES//2, curses.LINES)


def rain(stdscr, pool):
    while True:
        x = random.choice(pool)
        pool.remove(x)
        max_length = random_rain_length()
        speed = random.randint(1, options['speed'])
        yield from animate_rain(stdscr, x, max_length, speed)
        pool.append(x)


def animate_rain(stdscr, x, max_length, speed=FALLING_SPEED):
    """
    A rain consists of 3 parts: head, body, and tail
    Head: the white leading rain drop
    Body: the fading trail
    Tail: empty space behind the rain trail

    :param stdscr: curses's screen object
    :param x: the column of this rain on the screen
    :param max_length: the length of this rain
    :param speed: how fast a rain should fall (the number of lines it jumps each animation frame)
    :return: None
    """
    head, middle, tail = 0, 0, 0

    while tail < curses.LINES:
        middle = head - max_length//2
        if (middle < 0):
            middle = 0

        tail = head - max_length
        if tail < 0:
            tail = 0
        else:
            show_tail(stdscr, tail, x, speed)

        show_body(stdscr, head, middle, tail, x)

        show_head(stdscr, head, x)

        head = head + speed
        yield


def show_head(stdscr, head, x):
    if head < curses.LINES:
        stdscr.addstr(head, x, random_char(), options['head'])


def show_body(stdscr, head, middle, tail, x):
    if USE_GRADIENT:
        for i in range(tail, min(head, curses.LINES)):
            stdscr.addstr(i, x, random_char(), get_color(i, head, tail))
    else:
        for i in range(tail, min(middle, curses.LINES)):
            stdscr.addstr(i, x, random_char(), curses.color_pair(1))
        for i in range(middle, min(head, curses.LINES)):
            stdscr.addstr(i, x, random_char(), curses.color_pair(1) | curses.A_BOLD)


def show_tail(stdscr, tail, x, speed):
    for i in range(max(0, tail - speed), min(tail, curses.LINES)):
        stdscr.addstr(i, x, ' ', curses.color_pair(0))


def get_color(i, head, tail):
    color_num = NUMBER_OF_COLOR - (head - i) + 1
    if color_num < 0:
        color_num = 0
    return curses.color_pair(START_COLOR_NUM + color_num)


def update_style():
    '''
    Cycle thru different styles
    :return: None
    '''
    options['head'] =  HEAD_BOLD if options['head'] == HEAD_STANDOUT else HEAD_STANDOUT


def main(stdscr):
    stdscr.addstr(0, 0, "Press any key to start. Press any key (except SPACE) to stop.")
    stdscr.addstr(1, 0, "Press key 'h' to try a different style.")
    stdscr.addstr(curses.LINES//3, curses.COLS//4, "T H E   M A T R I X")
    ch = stdscr.getch()  # Wait for user to press something before starting
    config(stdscr)

    rains = []
    pool = list(range(curses.COLS - 1))

    while True:
        add_rain(rains, stdscr, pool)

        for r in rains:
            next(r)

        ch = stdscr.getch()
        if ch != curses.ERR and ch != ord(' '):  # Use space to proceed animation if nodelay is False
            if ch == ord('h'):
                update_style()
            else:
                break  # exit

        time.sleep(SLEEP_BETWEEN_FRAME)


def add_rain(rains, stdscr, pool):
    if (len(rains) < options['count']) and (len(pool) > 0):
        rains.append(rain(stdscr, pool))


if __name__ == "__main__":
    curses.wrapper(main)
