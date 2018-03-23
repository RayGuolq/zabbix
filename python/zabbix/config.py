# log config
LOGGER_NAME = 'zabbixlogger'
#LOG_FILE = '/var/log/zabbix.log'
LOG_FILE = 'zabbix.log'
LOG_FILE_FORMAT = '%(asctime)s, %(process)d, %(levelname)s, %(filename)s:%(funcName)s:%(lineno)d, %(message)s'
LOG_SYSERR_FORMAT = '%(asctime)s: %(message)s'


# DB
#MONGO_HOST='127.0.0.1'
#MONGO_PORT=27017
#MONGO_USER='root'
#MONGO_PASSWORD='password'
#MONGO_DB_NAME='zabbix'


#PID_FILE='/var/run/iwiot/pid'
#LOCK_FILE='/var/run/iwiot/lock'
PID_FILE='.pid'
LOCK_FILE='.lock'


# ZABBIX
ZABBIX_HOST                    = "192.168.1.1"
ZABBIX_PORT                    = 8000
ZABBIX_USER                    = "Admin"
ZABBIX_PASSWORD                = "zabbix"
ZABBIX_URL                     = "http://%s:%d/zabbix/api_jsonrpc.php" % (ZABBIX_HOST,ZABBIX_PORT)
ZABBIX_JSONRPC_VERSION         = "2.0"
ZABBIX_HOSTGROUP_NAME          = "Tahoe devices"
ZABBIX_TEMPLATE_NAME           = "Tahoe device template"
ZABBIX_USERGROUP_NAME          = "Tahoe users"

