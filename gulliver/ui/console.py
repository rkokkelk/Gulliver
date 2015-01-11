
from threading import Thread
import utils
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
        header = "%s %s Console" % (utils.get_name(),utils.get_version())

        stascr = curses.newwin(1, curses.COLS, curses.LINES-2,0)
        inpscr = curses.newwin(1, curses.COLS, curses.LINES-1,0)
        logscr = curses.newpad(curses.LINES-3,curses.COLS-1)
        self.stdscr = stdscr
        self.logscr = logscr
        self.stascr = stascr
        self.inpscr = inpscr

        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_BLUE)

        curses.echo()

        stdscr.bkgd(' ', curses.color_pair(1))
        stascr.bkgd(' ', curses.color_pair(1))

        stdscr.addstr(0,0,header)
        logscr.addstr(0,0,"Second window!")
        inpscr.keypad(True)

        stdscr.refresh()
        logscr.refresh(0,0,1,0,curses.LINES-3,curses.COLS-1)
        inpscr.refresh()


        input_thread = consoleInput(inpscr,self)
        input_thread.start()

    def update_status(self, status):
        self.stascr.addstr(0,0,status)
        self.stascr.refresh()

    def update_log(self, log):

        self.index+= 1

        self.logscr.addstr(self.index,0,log)
        self.logscr.refresh(0,0,1,0,curses.LINES-3,curses.COLS-1)

    def exit(self):
        curses.endwin()
        curses.nocbreak();
        curses.echo()
        self.inpscr.keypad(False)
        exit(0)

class consoleInput(Thread):

    def __init__(self, input_screen, ui):
        Thread.__init__(self)
        self.input_screen = input_screen
        self.ui = ui

    def run(self):

        import curses

        while True:
            in_text = self.input_screen.getstr(0,0,curses.COLS)

            if 'quit' in in_text:
                break
            else:
                self.ui.update_log(in_text)

        self.ui.exit()
