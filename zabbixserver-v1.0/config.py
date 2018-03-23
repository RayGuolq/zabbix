# log config
LOGGER_NAME = 'zabbixlogger'
#LOG_FILE = '/var/log/zabbix.log'
LOG_FILE = 'zabbix.log'
LOG_FILE_FORMAT = '%(asctime)s, %(process)d, %(levelname)s, %(filename)s:%(funcName)s:%(lineno)d, %(message)s'
LOG_SYSERR_FORMAT = '%(asctime)s: %(message)s'

WEB_SERVICE_HOST = ""
WEB_SERVICE_PORT = 1111

ZABBIX_SERVER_HOST = '192.168.1.1'

# DB
MYSQL_HOST='127.0.0.1'
MYSQL_PORT=3306
MYSQL_USER='user'
MYSQL_PASSWORD='password'
MYSQL_DB_NAME='demoDB'


#PID_FILE='/var/run/zabbix/pid'
#LOCK_FILE='/var/run/zabbix/lock'
PID_FILE='.pid'
LOCK_FILE='.lock'

