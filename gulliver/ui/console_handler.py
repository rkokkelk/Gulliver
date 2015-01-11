import logging

log = logging.getLogger('gulliver.test')

class ProgressConsoleHandler(logging.Handler):
    """
    A handler class which allows the cursor to stay on
    one line for selected messages
    """
    on_same_line = False
    console = None

    def __init__(self, console):
        logging.Handler.__init__(self)
        self.console = console

    def emit(self, record):
        try:
            msg = self.format(record)
            #self.console.update_log(msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
