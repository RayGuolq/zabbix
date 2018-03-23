#!/usr/bin/env python
#coding: utf-8
import sys
import requests
import logging

LOGGER_NAME = 'smslogger'
#LOG_FILE = '/var/log/zabbix/sms.log'
LOG_FILE = 'sms.log'
LOG_FILE_FORMAT = '%(asctime)s, %(process)d, %(levelname)s, %(filename)s:%(funcName)s:%(lineno)d, %(message)s'
LOG_SYSERR_FORMAT = '%(asctime)s: %(message)s'
LOG_LEVEL = logging.DEBUG

logger = logging.getLogger(LOGGER_NAME)

log_file_formatter = logging.Formatter(LOG_FILE_FORMAT)
log_file_handler = logging.FileHandler(LOG_FILE)
log_file_handler.setFormatter(log_file_formatter)
logger.addHandler(log_file_handler)

log_syserr_formatter = logging.Formatter(LOG_SYSERR_FORMAT)
syserr_handler = logging.StreamHandler(sys.stderr)
syserr_handler.setFormatter(log_syserr_formatter)
logger.addHandler(syserr_handler)

logger.setLevel(LOG_LEVEL)


# configurations
SMS_CLIENT_ID   = 300
SMS_CLIENT_NAME = "iwater"
SMS_PASSWORD    = "9E24A3C12963A4EA0311C69B3E7D6B03" # MD5 hashed password
SMS_SERVICE_URL = "http://sms.bdt360.com:8180/service.asmx/SendMessageStr"

class SMSSender:
    def __init__(self):
        pass

    def send(self, mobile, message):
        def check_rsp(rsp):
            """
            Response format: State:1,Id:11811665,FailPhone:
            """
            success = False
            for i in rsp.split(','):
                if i.find('State:') >= 0:
                    status= int(i.split(':')[1])
                    if status == 1:
                        success = True
            return success

        logger.info("send message[%s], to mobile[%s]" % (message, mobile))
        try:
            params = {'Id':SMS_CLIENT_ID,
                      'Name':SMS_CLIENT_NAME,
                      'Psw':SMS_PASSWORD,
                      'Message':message,
                      'Phone':mobile,
                      'Timestamp':0}
            rsp = requests.post(SMS_SERVICE_URL, data=params)
        except Exception as e:
            logger.error("send SMS failure: %s" % e.message)
            return False

        success = check_rsp(rsp.text)
        if success:
            logger.debug("send SMS to [%s] succeeded" % mobile)
        else:
            logger.error("send SMS to [%s] failed" % mobile)
        return success

if __name__ == "__main__":
    ## this should succeed
    #mobile = "18616764280"
    #message = u"【贞泉】您的验证码是：abc，请妥善保管，谢谢！"
    """
    zabbix default 3 parameters:
      arg1: mobile, arg2:subject, arg3:message
    """
    mobile = sys.argv[1]
    subject = sys.argv[2]
    message = sys.argv[3]
    sender = SMSSender()
    success = sender.send(mobile, message)
