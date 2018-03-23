import config
import time
import mysql.connector
from threading import Lock
from utils import get_logger, timestamp_to_str, datetime_to_timestamp

########################################
# MysqlDB
########################################

logger = get_logger()

db_lock = Lock()

db_connection = None

# setup DB connection
def get_db_connection():
    logger.debug("Getting DB connection")
    db_lock.acquire()
    global db_connection
    if db_connection != None:
        db_lock.release()
        logger.debug("DB connection successfully get")
        return db_connection
    try:
        db_connection = mysql.connector.connect(user=config.MYSQL_USER, \
                                          password=config.MYSQL_PASSWORD, \
                                          host=config.MYSQL_HOST, \
                                          port=config.MYSQL_PORT, \
                                          database=config.MYSQL_DB_NAME)
    except mysql.connector.Error, e:
        logger.error("Connecting to DB [%s] connection failed: %s" % \
                     (config.MYSQL_DB_NAME, str(e)))
    except Exception, e:
        logger.error("Connecting to DB [%s] connection failed: %s" % \
                     (config.MYSQL_DB_NAME, e.message))
    db_lock.release()
    logger.debug("DB connection successfully get")

    return db_connection

def db_close(conn):
    logger.debug("Closing DB")
    db_lock.acquire()
    if conn:
        conn.close()
    db_lock.release()
    logger.debug("DB closed")

def db_execute(conn, operation, params=None):
    result = False
    cursor = None
    logger.debug("Executing DB command: %s" % operation)
    db_lock.acquire()
    try:
        if not conn.is_connected():
            logger.debug("Reconnect DB")
            conn.reconnect()
        cursor = conn.cursor()
        cursor.execute(operation, params=params)
        conn.commit()
        result = True
    except mysql.connector.Error, e:
        logger.error("Error executing DB command: %s, error: %s" % \
                     (operation, str(e)))
    except Exception, e:
        logger.error("Error executing DB command: %s, error: %s" % \
                     (operation, e.message))
        result = False
    finally:
        if cursor:
            cursor.close()
    db_lock.release()
    return result

def db_query(conn, query, params=None):
    result = []
    cursor = None
    logger.debug("Executing DB query: %s" % query)
    db_lock.acquire()
    try:
        if not conn.is_connected():
            logger.debug("Reconnect DB")
            conn.reconnect()
        cursor = conn.cursor()
        cursor.execute(query, params=params)
        result = cursor.fetchall()
        conn.commit()
    except mysql.connector.Error, e:
        logger.error("Connecting to DB [%s] connection failed: %s" % \
                     (query, str(e)))
    except Exception, e:
        logger.error("Error querying DB: %s, error: %s" % \
                     (query, e.message))
    finally:
        if cursor:
            cursor.close()
    db_lock.release()
    return result
########################################
# MysqlDB section end
########################################

########################################
# DeviceStore
########################################

DEVICE_STATUS_ONLINE = 3

class DeviceStore(object):
    def __init__(self):
        logger.debug("initialize DeviceStore")
        self.conn = get_db_connection()

    def get_logical_address_by_hashkey(self, hashkey):
        """
        Get the device logical address from the DB.

        Input:
        * hashkey: device hash key.

        Output:
        * logical_address: device logical address
        """
        logger.debug("Executing get()")
        device = None
        query_cmd="select logical_address from device where device_hash_key='%s' and status=%d" % (hashkey, DEVICE_STATUS_ONLINE)
        result = db_query(self.conn, query_cmd)

        if result:
            logical_address = result[0][0]
            logger.info("Get device logical_address by device_hash_key[%s] query succeed" % hashkey)
        else:
            logger.error("Get device logical_address by device_hash_key[%s] query failed" % hashkey)

        return logical_address

# single instance
device_store_instance = None
device_store_lock = Lock()

def get_device_store():
    """
    Get the global device controller instance.
    """
    device_store_lock.acquire()
    global device_store_instance
    if device_store_instance == None:
        device_store_instance = DeviceStore()
    device_store_lock.release()
    return device_store_instance

if __name__ == "__main__":
    #device_store = get_device_store()
    #timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    #device_store.add('s81',2,1,'s81','111111',1,'111111',timestamp)
    #print device_store.get('111111')
    #device_store.save_data('111111',"data1",timestamp)
    #print device_store.get_datas("111111","2016-07-01 15:10:55","2016-07-4 15:15:55")
    pass
########################################
# DeviceStore section end
########################################
