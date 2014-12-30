

import logging
import curses
import time
    
log = logging.getLogger('gulliver.console')

class consoleUI():

    stdscr = None
    logscr = None
    index = 0

    def __init__(self):
        log.debug("Init")
        curses.wrapper(self.run)

    def run(self,stdscr):

        log.debug("Screen run started")
        logscr =  curses.newwin(curses.LINES -3, curses.COLS - 3, 1,1)
        self.stdscr = stdscr
        self.logscr = logscr
        curses.use_default_colors()

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_BLUE)
        stdscr.bkgd(' ', curses.color_pair(1))
        stdscr.border(0)
        #stdscr.border(1,1,1,1,1,1,1,1)

        stdscr.addstr(0,0,"NCurses has started")

        logscr.addstr(0,0,"Second window!")
        stdscr.refresh()
        logscr.refresh()

    def update_status(self, status):
        self.stdscr.addstr(curses.LINES-1,0,status)
        self.stdscr.refresh()

    def update_log(self, log):

        self.logscr.addstr(1,0,log+"\n")
        self.logscr.refresh()

    def exit(self):
        curses.endwin()
        curses.initscr()

