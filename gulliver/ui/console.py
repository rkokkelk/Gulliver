
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
    index = -1
    y = 0

    input_run = True

    def __init__(self, lt_session):
        global y

        y = 0
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
        logscr = curses.newpad(30000,curses.COLS-1)
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
        inpscr.keypad(True)

        stdscr.refresh()
        logscr.refresh(0,0,1,0,curses.LINES-3,curses.COLS-1)
        inpscr.refresh()

    def update_status(self, status):
        self.stascr.addstr(0,0,status)
        self.stascr.noutrefresh()

    def clear_logscr(self):

        self.index = 0 -1

        self.logscr.clear()
        self.logscr.refresh(0,0,1,0,curses.LINES-3,curses.COLS-1)


    def update_log(self, log):

        self.index += 1
        self.logscr.addstr(self.index,0,log)
        self.log_refresh()

    def log_refresh(self):
        global y
        i = max(y,0)
        self.logscr.refresh(i,0,1,0,curses.LINES-3,curses.COLS-1)

    def exit(self):
        curses.endwin()
        curses.nocbreak();
        curses.noecho()
        self.inpscr.keypad(False)

    def scroll_down(self):
        global y
        y += 1
        self.logscr.addstr(self.index,0,str(y))
        self.log_refresh()

    def scroll_up(self):
        global y
        y -= 1
        self.logscr.addstr(self.index,0,str(y))
        self.log_refresh()

class consoleInput(Thread):


    def __init__(self, ui):
        Thread.__init__(self)
        self.input_screen = ui.inpscr
        self.lt_session = ui.get_libtorrent_session()
        self.ui = ui

    def run(self):

        import curses

        cmd_input = ""
        screen = self.input_screen
        screen.refresh()

        while True:
            c = screen.getch()
            #in_text = screen.getstr(0,0,curses.COLS)
            #self.ui.logscr.addstr(0,0,str(c))

            KEY_UP, KEY_DOWN = 'AB'
            if c == curses.KEY_HOME or c == 10:

                if not self.analyse_input(cmd_input):
                    break

                cmd_input = ""
                self.clear_input()

            elif c == KEY_DOWN or str(c) == 'd':
                self.ui.scroll_down()
            elif c == KEY_UP or str(c) == 'u':
                self.ui.scroll_up()
            else:
                cmd_input += chr(c)

        self.ui.exit()

    def clear_input(self):
        self.input_screen.clear()
        self.input_screen.refresh()

    def analyse_input(self, cmd_input):

        if 'quit' in cmd_input:
            return False

        elif 'settings' in cmd_input:

            settings = self.lt_session.get_settings()

            for k in settings:
                v = settings[k]

                if isinstance(v,str):
                    if v:
                        v = ""
                #status = "{0} = {1}".format(k,str(v).encode("hex"))
                status = "{0} = {1}".format(k,v)

                self.ui.update_log(str(status))

        elif 'clear' in cmd_input:
            self.ui.clear_logscr()

        elif 'save' in cmd_input:
            self.lt_session.save_settings('libtorrent.settings')
            self.ui.update_log("Libtorrent settings saved")

        elif 'load' in cmd_input:
            self.lt_session.load_settings('libtorrent.settings')
            self.ui.update_log("Libtorrent settings loaded")

        else:
            self.ui.update_log(cmd_input)

        return True

