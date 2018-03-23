import zabbix.config as config
import logging
import os
import string
import random
import sys
import time
import pickle

from threading import Lock


#log_level = logging.INFO
log_level = logging.DEBUG

# logger instance
logger = None
logger_lock = Lock()

def get_logger():
    global logger
    logger_lock.acquire()
    try:
        if logger is None:
            logger = logging.getLogger(config.LOGGER_NAME)
            
            log_file_formatter = logging.Formatter(config.LOG_FILE_FORMAT)
            log_file_handler = logging.FileHandler(config.LOG_FILE)
            log_file_handler.setFormatter(log_file_formatter)
            logger.addHandler(log_file_handler)
            
            log_syserr_formatter = logging.Formatter(config.LOG_SYSERR_FORMAT)
            syserr_handler = logging.StreamHandler(sys.stderr)
            syserr_handler.setFormatter(log_syserr_formatter)
            logger.addHandler(syserr_handler)
            
            logger.setLevel(log_level)
    except Exception as e:
        sys.stderr.write("Get logger failed")
        logger = None
    finally:
        logger_lock.release()
    return logger

def get_log_level():
    return log_level

def set_log_level(level):
    global logger, log_level
    logger.setLevel(level)
    log_level = level

def hex_dump(data):
    logger.debug("==========  HEX dump ==========")
    logger.debug("Length: %d" % len(data))
    hex_str = '0x'
    for byte in data:
        hex_str += byte.encode('hex')
    logger.debug(hex_str)
    logger.debug("===============================")

class LockedMap:
    def __init__(self):
        self.lock = Lock()
        self.data_map = {}

    def add(self, key, value):
        """
        Add an element of key/value pair to the map
        """
        self.lock.acquire()
        if not self.data_map.has_key(key):
            self.data_map[key] = value
        self.lock.release()

    def delete(self, key):
        """
        Delete the element related with 'key'.
        """
        self.lock.acquire()
        if self.data_map.has_key(key):
            del self.data_map[key]
        self.lock.release()

    def find(self, key):
        """
        Find out the element related with the 'key'
        """
        ret = None
        self.lock.acquire()
        if self.data_map.has_key(key):
            ret = self.data_map[key]
        self.lock.release()
        return ret

    def pop(self, key):
        """
        Pop out the element related with 'key'
        """
        ret = None
        self.lock.acquire()
        ret = self.data_map.pop(key, None)
        self.lock.release()
        return ret

    def all_values(self):
        ret = None
        self.lock.acquire()
        ret = self.data_map.values()
        self.lock.release()
        return ret

class LockedList:
    def __init__(self, name = ''):
        if name != '':
            self.name = name
        else:
            self.name = "LockedList"
        self.lock = Lock()
        self.data_list = []

    def append(self, data):
        """
        Append an element to the tail of the list
        """
        if data is None:
            return
        self.lock.acquire()
        self.data_list.append(data)
        self.lock.release()

    def remove(self, data):
        """
        Delete the element
        """
        self.lock.acquire()
        try:
            self.data_list.remove(data)
        except ValueError, e:
            logger.error("LockedList [%s] remove error: data doesn't exist" % self.name)
        except Exception as e:
            logger.error("LockedList [%s] remove error: %s" % (self.name, e.message))
        self.lock.release()

    def pop(self, index=0):
        """
        Pop out the element referred by the 'index'

        Input:
        * index: element of the index, 0 by default (pop out the 1st one)

        Output:
        * element: the element to be returned, None if the list is empty.
        """
        ret = None
        self.lock.acquire()
        try:
            ret = self.data_list.pop(index)
        except IndexError, e:
            #logger.debug("LockedList [%s] pop error: list is empty" % self.name)
            # ignore the list empty exception
            pass
        except Exception as e:
            logger.error("LockedList [%s] pop error: %s" % (self.name, e.message))
        self.lock.release()
        return ret

    def empty(self):
        return len(self.data_list)==0

    def exist(self, data):
        ret = False
        self.lock.acquire()
        try:
            idx = -1
            idx = self.data_list.index(data)
            if idx >= 0:
                ret = True
        except Exception:
            ret = False
        self.lock.release()
        return ret

# make a the process a daemon. If any error happen, it will raise an exception.
def daemonize(root_dir="/", \
              pidfile="", \
              stdin="/dev/null", \
              stdout="/dev/null", \
              stderr="/dev/null"):
    '''
    Make the process into a daemon
    '''
    # Perform the first fork.
    try:
        pid = os.fork()
        if pid > 0:
            # Directly exit first parent without SystemExit exception
            os._exit(0)
    except OSError, excep:
        msg = "fork failed: (%d) %s" % (excep.errno, excep.strerror)
        logger.error(msg)
        raise(Exception(msg))

    # Decouple from parent environment.
    try:
        os.chdir(root_dir)
    except OSError, excep:
        msg = "chdir(%s) failed: (%d) %s" % (root_dir, excep.errno, excep.strerror)
        logger.error(msg)
        raise(Exception(msg))

    try:
        os.umask(0)
    except OSError, excep:
        msg = "umask failed: (%d) %s" % (excep.errno, excep.strerror)
        logger.error(msg)
        raise(Exception(msg))

    try:
        os.setsid()
    except OSError, excep:
        msg = "setsid failed: (%d) %s" % (excep.errno, excep.strerror)
        logger.error(msg)
        raise(Exception(msg))

    # Perform the second fork.
    try:
        pid = os.fork()
        if pid > 0:
            # Directly exit second parent without SystemExit exception
            os._exit(0)
    except OSError, excep:
        msg = "fork failed: (%d) %s" % (excep.errno, excep.strerror)
        logger.error(msg)
        raise(Exception(msg))

    # The process is now daemonized, redirect standard file descriptors.
    for filedesc in sys.stdout, sys.stderr:
        filedesc.flush()
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)

    try:
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
    except OSError, excep:
        msg = "dup2 failed: (%d) %s" % (excep.errno, excep.strerror)
        logger.error(msg)
        raise(Exception(msg))

    # Create the pid file if specified
    if pidfile != "":
        # remove any existing one before create the new one
        try:
            if os.path.exists(pidfile):
                os.remove(pidfile)
        except OSError, e:
            msg = "Remove pid file [%s] failure: %s" % (pidfile, e.strerror)
            logger.error(msg)
            raise(Exception(msg))
        except Exception as e:
            msg = "Remove pid file [%s] failure: %s" % (pidfile, e.message)
            logger.error(msg)
            raise(Exception(msg))
        try:
            pidfile_fd = open(pidfile, "w")
            pidfile_fd.write("%d" % os.getpid())
            pidfile_fd.close()
        except Exception as e:
            msg = "Create pid file [%s] failure: %s" % (pidfile, e.message)
            logger.error(msg)
            raise(Exception(msg))

def checksum(data):
    checksum = 0
    # calculate the data part
    for b in bytearray(data):
        checksum += b
    checksum &= 0xff
    return checksum

TIME_FORMAT_STR = "%Y-%m-%d %H:%M:%S"

def timestamp_to_str(timestamp):
    ret = time.strftime(TIME_FORMAT_STR, time.localtime(timestamp))
    return ret

def str_to_timestamp(tm_str):
    ret = time.mktime(time.strptime(tm_str, TIME_FORMAT_STR))
    return ret

def datetime_to_timestamp(date_time):
    return str_to_timestamp(str(date_time))


CHAR_COLLECTION = string.letters + string.digits + string.punctuation

def random_chars(length=1):
    result = ""
    for i in range(length):
        result += random.choice(CHAR_COLLECTION)
    return result


BASE_ID_DIR="./.genid"
id_generator_lock = Lock()

def gen_id(app):
    id_generator_lock.acquire()
    try:
        id_dir = "%s/%s" % (BASE_ID_DIR, app)
        if not os.access(id_dir, os.R_OK|os.W_OK):
            os.makedirs(id_dir)
    
        id_file = "%s/.id" % id_dir
        if os.access(id_file, os.R_OK|os.W_OK):
            fd = open(id_file, 'rb')
            last_id = pickle.load(fd)
            fd.close()
        else:
            last_id = 0

        new_id = last_id + 1
        fd = open(id_file, 'wb')
        pickle.dump(new_id, fd)
        fd.close()
    except Exception as e:
        logger.error("generate ID for app[%s] failure: %s" % (app,
            e.message))
        raise
    finally:
        id_generator_lock.release()
    return new_id

def gen_letter_label(lable_suffix, num):
    """
    Input:
    * lable_suffix: a letter label of suffix
    * num: a digit
    Output:
    * letter_label: a letter label, for example: A or B or AB
    """
    num = int(num)
    if num < 1:
        return "A"

    upper_letters=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P', \
            'Q','R','S','T','U','V','W','X','Y','Z']
    num_1 = num/26
    num_2 = num%26
    if num_1 > 0:
        lable_suffix = upper_letters[num_2-1] + lable_suffix
        return gen_letter_label(lable_suffix, num_1)
    else:
        return upper_letters[num_2-1] + lable_suffix

def encode_multipart_formdata(fields, files=[]):
    """
    fields is a sequence of (name, value, content-type) elements for regular form fields.
    files is a sequence of (name, filepath, filedata, content-type) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    import mimetools
    BOUNDARY = mimetools.choose_boundary()
    CRLF = '\r\n'
    L = []
    for (key, value, ctype) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('Content-Type: %s' % ctype)
        L.append('')
        L.append(value)
    for (key, filepath, filedata, ctype) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filepath))
        L.append('Content-Type: %s' % ctype)
        L.append('')
        L.append(filedata)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body
