
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
    lt_session = None
    index = 0

    input_run = True

    def __init__(self, lt_session):
        log.debug("Init")
        curses.wrapper(self.run)
        self.lt_session = lt_session

    def get_libtorrent_session(self):
        return self.lt_session

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

    def update_status(self, status):
        self.stascr.addstr(0,0,status)
        self.stascr.noutrefresh()

    def update_log(self, log):

        self.index+= 1

        self.logscr.addstr(self.index,0,log)
        self.logscr.refresh(0,0,1,0,curses.LINES-3,curses.COLS-1)

    def exit(self):
        curses.endwin()
        curses.nocbreak();
        curses.echo()
        self.inpscr.keypad(False)

class consoleInput(Thread):


    def __init__(self, ui):
        Thread.__init__(self)
        self.input_screen = ui.inpscr
        self.lt_session = ui.get_libtorrent_session()
        self.ui = ui

    def run(self):

        import curses

        screen = self.input_screen
        screen.refresh()

        while True:
            in_text = screen.getstr(0,0,curses.COLS)
            screen.refresh()

            if 'quit' in in_text:
                break

            elif 'settings' in in_text:

                settings = self.lt_session.get_settings()

                for k in settings:
                    v = settings[k]
                    v = "test"
                    status = "{0} = {1}({1})".format(k,v,type(v))
                    #log.info(status)

                    self.ui.update_log(status)
                
                self.clear_input()

            elif 'clear' in in_text:
                self.ui.stascr.clear()
                self.ui.stascr.refresh()
                self.clear_input()

            elif 'save' in in_text:
                self.lt_session.save_settings('libtorrent.settings')
                self.ui.update_log("Libtorrent settings saved")
                self.clear_input()

            elif 'load' in in_text:
                self.lt_session.load_settings('libtorrent.settings')
                self.ui.update_log("Libtorrent settings loaded")
                self.clear_input()

            else:
                self.ui.update_log(in_text)
                self.clear_input()

        self.ui.exit()

    def clear_input(self):
        self.input_screen.clear()
        self.input_screen.refresh()

