
import logging
import curses
import time
    
log = logging.getLogger('gulliver.console')

class consoleUI():

    stdscr = None
    logscr = None
    stascr = None
    inpscr = None
    index = 0

    def __init__(self):
        log.debug("Init")
        curses.wrapper(self.run)

    def run(self,stdscr):

        log.debug("Screen run started")
        header = "%s %s Console" % (Gulliver.name,Gulliver.version)

        logscr = curses.newwin(curses.LINES-3, curses.COLS, 1,0)
        stascr = curses.newwin(1, curses.COLS, curses.LINES-2,0)
        inpscr = curses.newwin(1, curses.COLS, curses.LINES-1,0)
        self.stdscr = stdscr
        self.logscr = logscr
        self.stascr = stascr
        self.inpscr = inpscr

        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_BLUE)

        stdscr.bkgd(' ', curses.color_pair(1))
        stascr.bkgd(' ', curses.color_pair(1))

        stdscr.addstr(0,0,header)
        logscr.addstr(0,0,"Second window!")

        stdscr.refresh()
        logscr.refresh()

    def update_status(self, status):
        self.stascr.addstr(0,0,status)
        self.stascr.refresh()

    def update_log(self, log):

        self.logscr.addstr(0,0,log+"\n")
        self.logscr.refresh()

    def exit(self):
        curses.endwin()
