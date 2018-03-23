import config
import fcntl
import signal
import os
import sys
import time
from optparse import OptionParser
from api import APIService
from utils import logger, daemonize

class Server:
    def __init__(self):
        self.api_server = APIService(config.WEB_SERVICE_HOST, config.WEB_SERVICE_PORT)
        self.running = False

    # register the signal handler
    def register_signal_handler(self):
        '''
        Register the signal handler
        '''
        def agent_signal_handler(signum, frame):
            '''
            Agent signal handler
            '''
            logger.debug("Server terminate signal is received")
            self.stop()

        signal.signal(signal.SIGINT, agent_signal_handler)
        signal.signal(signal.SIGTERM, agent_signal_handler)
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    def start(self):
        logger.info("Starting the server")
        try:
            self.register_signal_handler()
            self.api_server.start()
            self.running = True
        except Exception as e:
            logger.error("Error starting the server, error: %s", e.message)
            self.running = False
            raise
        logger.info("Server started")

    def stop(self):
        logger.info("Stopping the server")
        try:
            self.running = False
            self.api_server.stop()
        except Exception as e:
            logger.error("Error stopping the server, exit now. Error: %s" %
                    e.message)
            os._exit(3)
        logger.info("Server stopped")
        sys.exit(0)

    def loop(self):
        # server loop
        while self.running:
            time.sleep(1)

def parse_command_line():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--daemon", action="store_true", dest="daemonize",
                      default=False,
                      help="Run the server as daemon.")

    (options, args) = parser.parse_args()
    return (options, args)

def main():
    # Check the lockfile to make sure there is only one instance running
    lockfile_fd = open(config.LOCK_FILE, "a+")
    try:
        fcntl.flock(lockfile_fd.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
    except IOError, e:
        logger.error("lock file (%s) failed, (%d) %s" % \
                     (config.LOCK_FILE, e.errno, e.strerror))
        os._exit(1)

    options, metadataXMLFile = parse_command_line()
    if options.daemonize:
        logger.info("Run the server in daemon mode")
        daemonize("/", config.PID_FILE)
    else:
        logger.info("Run the server in interactive mode")

    try:
        server = Server()
        server.start()
    except Exception:
        logger.error("Start server failure")
        os._exit(2)
    server.loop()

    return 0

if __name__ == "__main__":
    main()
    sys.exit(0)
