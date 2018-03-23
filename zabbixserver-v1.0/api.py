import os
import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.concurrent
import json

import config

from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from utils import get_logger
from db import get_device_store
from exception import InvalidParameterException


API_VERSION = "v1"
BASE_URL = "/zabbix/api/%s" % API_VERSION


EXECUTOR = ThreadPoolExecutor(max_workers=10)

RSP_KEY_STATUS = 'status'
RSP_KEY_MESSAGE = 'message'
RSP_KEY_DATA = 'data'

RSP_STATUS_SUCCESS = 0
RSP_STATUS_FAILURE = 1
RSP_STATUS_EEXIST = 17
RSP_STATUS_INVALID_PARAMETER = 2

RSP_MESSAGE_SUCCESS = 'success'
RSP_MESSAGE_FAILURE = 'failure'

HEADER_CONTENT_TYPE = "Content-Type"
CONTENT_TYPE_JSON = "application/json"

logger = get_logger()


class BaseHandler(tornado.web.RequestHandler):
    executor = EXECUTOR

    def prepare(self):
        try:
            content_type = self.request.headers.get(HEADER_CONTENT_TYPE)
            if content_type != None and \
                    content_type.lower().startswith(CONTENT_TYPE_JSON):
                if self.request.body.strip() != "":
                    self.json_args = json.loads(self.request.body)
                else:
                    self.json_args = None
            else:
                self.json_args = None
        except ValueError:
            message = "Invalid request: %s" % self.request.body
            log_message = "[%s] %s:%s, %s" % (self.request.remote_ip, \
                                              self.request.method, \
                                              self.request.path, \
                                              message)
            logger.info(log_message)
            response = self.make_response(RSP_STATUS_INVALID_PARAMETER, \
                                          message)
            self.finish(response)
        except Exception as e:
            log_message = "[%s] %s:%s, %s" % (self.request.remote_ip, \
                                              self.request.method, \
                                              self.request.path, \
                                              e.message)
            logger.info(log_message)
            raise

    def make_response(self, status, message="", data=None):
        if not isinstance(status, int) or status < 0:
            raise InvalidParameterException("status")
        if not isinstance(message, str):
            raise InvalidParameterException("message")

        response = dict()
        response[RSP_KEY_STATUS] = status
        if status == RSP_STATUS_SUCCESS:
            if message == "":
                response[RSP_KEY_MESSAGE] = RSP_MESSAGE_SUCCESS
            else:
                response[RSP_KEY_MESSAGE] = message
        else:
            if message == "":
                response[RSP_KEY_MESSAGE] = RSP_MESSAGE_FAILURE
            else:
                response[RSP_KEY_MESSAGE] = message
        if data != None:
            response[RSP_KEY_DATA] = data

        return response

    def log_request(self):
        if self.json_args:
            log_message = "[%s] %s:%s, %s" % (self.request.remote_ip, \
                                                  self.request.method, \
                                                  self.request.path, \
                                                  repr(self.json_args))
        else:
            log_message = "[%s] %s:%s" % (self.request.remote_ip, \
                                                  self.request.method, \
                                                  self.request.path)
        logger.info(log_message)


class DeviceDataHandler(BaseHandler):
    DATA_TYPE_STRING = 'string'
    POST_REQUEST_KEY_HEADER = 'header'
    POST_REQUEST_KEY_EVENT = 'event'
    POST_REQUEST_KEY_ENDPOINTKEYHASH = 'endpointKeyHash'

    ITEM_KEY_TDS = "device.tds"
    ITEM_KEY_RUNNING_STATUS = "device.running_status"
    ITEM_KEY_WATER_PURIFIED = "device.water_purified"
    ITEM_KEY_FILTER1_LIFE_PERCENT = "device.filter1_life_percent"
    ITEM_KEY_FILTER2_LIFE_PERCENT = "device.filter2_life_percent"
    ITEM_KEY_FILTER3_LIFE_PERCENT = "device.filter3_life_percent"
    ITEM_KEY_FILTER4_LIFE_PERCENT = "device.filter4_life_percent"
    ITEM_KEY_FILTER5_LIFE_PERCENT = "device.filter5_life_percent"
    ITEM_KEY_COLD_WATER_TEMP = "device.cold_water_temp"
    ITEM_KEY_HOT_WATER_TEMP = "device.hot_water_temp"

    @tornado.concurrent.run_on_executor
    def post(self):
        """
        Description: Receive and parse kaa device's data
        URL: {base_url}/data
        Method: POST
        Header:
          Content-Type = application/json
        Request:
        {
            "header": {
                "endpointKeyHash": {
                    "string": "xEmn1GGIK/AYOz8zMQFMWWmsLD4="
                },
                "applicationToken": {
                    "string": "14020583516186638298"
                },
                "headerVersion": {
                    "int": 1
                },
                "timestamp": {
                    "long": 1476940343424
                },
                "logSchemaVersion": {
                    "int": 10
                }
            },
            "event": {
                "inletTDS": 150,
                "outletTDS": 8,
                "hotWaterTemp": 98,
                "coldWaterTemp": 23,
                "waterPurified": 105,
                "workingStatus": 1,
                "failureStatus": 0,
                "filterStatus": {
                    "filterCount": 5,
                    "filterList": [
                        {
                            "life": 100,
                            "base": 360
                        },
                        {
                            "life": 200,
                            "base": 720
                        },
                        {
                            "life": 250,
                            "base": 720
                        },
                        {
                            "life": 789,
                            "base": 1440
                        },
                        {
                            "life": 567,
                            "base": 720
                        }
                    ]
                },
                "deviceConfig": {
                    "leaseConfig": {
                        "type": 1,
                        "periodStartTime": -1,
                        "periodEndTime": 31535999,
                        "volumeStart": 0,
                        "volumeTotal": 100
                    },
                    "monitorPolicy": {
                        "periodInfo": 0,
                        "periodWarning": 0,
                        "periodCritical": 0,
                        "volumeInfo": 0,
                        "volumeWarning": 0,
                        "volumeCritical": 0
                    },
                    "dataUploadInterval": 60,
                    "timestamp": 1472030058
                },
                "timestamp": -1
            }
        }

        Example:
          curl -v -X POST -H "Content-type: application/json" -d
          '{ "header" : { "endpointKeyHash" : { "string" : "xEmn1GGIK/AYOz8zMQFMWWmsLD4=" }, "applicationToken" : { "string" : "14020583516186638298" }, "headerVersion" : { "int" : 1 }, "timestamp" : { "long" : 1476940343424 }, "logSchemaVersion" : { "int" : 10 } }, "event" : { "inletTDS" : 150, "outletTDS" : 8, "hotWaterTemp" : 98, "coldWaterTemp" : 23, "waterPurified" : 105, "workingStatus" : 1, "failureStatus" : 0, "filterStatus" : { "filterCount" : 5, "filterList" : [ { "life" : 100, "base" : 360 }, { "life" : 200, "base" : 720 }, { "life" : 250, "base" : 720 }, { "life" : 789, "base" : 1440 }, { "life" : 567, "base" : 720 } ] }, "deviceConfig" : { "leaseConfig" : { "type" : 1, "periodStartTime" : -1, "periodEndTime" : 31535999, "volumeStart" : 0, "volumeTotal" : 100 }, "monitorPolicy" : { "periodInfo" : 0, "periodWarning" : 0, "periodCritical" : 0, "volumeInfo" : 0, "volumeWarning" : 0, "volumeCritical" : 0 }, "dataUploadInterval" : 60, "timestamp" : 1472030058 }, "timestamp" : -1 } }'
          http://localhost:11011/zabbix/api/v1/data
        """
        def zabbix_send_data(host_name, item_key, data):
            sender_command = "/bin/zabbix_sender -z %s -s '%s' -k %s -o %s" % (config.ZABBIX_SERVER_HOST, host_name, item_key, data)
            logger.info("zabbix sender command: %s" % sender_command)
            val = os.system(sender_command)
            return val
        def parse_data(data_map):
            item_key_values = []
            outletTDS = int(data_map["outletTDS"])
            item_key_values.append({"key":DeviceDataHandler.ITEM_KEY_TDS,"value":outletTDS})
            hotWaterTemp = int(data_map["hotWaterTemp"])
            item_key_values.append({"key":DeviceDataHandler.ITEM_KEY_HOT_WATER_TEMP,"value":hotWaterTemp})
            coldWaterTemp = int(data_map["coldWaterTemp"])
            item_key_values.append({"key":DeviceDataHandler.ITEM_KEY_COLD_WATER_TEMP,"value":coldWaterTemp})
            waterPurified = int(data_map["waterPurified"])
            item_key_values.append({"key":DeviceDataHandler.ITEM_KEY_WATER_PURIFIED,"value":waterPurified})
            failureStatus = int(data_map["failureStatus"])
            item_key_values.append({"key":DeviceDataHandler.ITEM_KEY_RUNNING_STATUS,"value":failureStatus})

            filter_list = data_map["filterStatus"]["filterList"]
            filter_life_percents = []
            for filter_one in filter_list:
                filter_life_percent = filter_one["life"]*100/filter_one["base"]
                filter_life_percents.append(filter_life_percent)
            if len(filter_life_percents) == 5:
                item_key_values.append({"key":DeviceDataHandler.ITEM_KEY_FILTER1_LIFE_PERCENT,"value":filter_life_percents[0]})
                item_key_values.append({"key":DeviceDataHandler.ITEM_KEY_FILTER2_LIFE_PERCENT,"value":filter_life_percents[1]})
                item_key_values.append({"key":DeviceDataHandler.ITEM_KEY_FILTER3_LIFE_PERCENT,"value":filter_life_percents[2]})
                item_key_values.append({"key":DeviceDataHandler.ITEM_KEY_FILTER4_LIFE_PERCENT,"value":filter_life_percents[3]})
                item_key_values.append({"key":DeviceDataHandler.ITEM_KEY_FILTER5_LIFE_PERCENT,"value":filter_life_percents[4]})
            return item_key_values

        self.log_request()

        try:
            header_map = self.json_args[DeviceDataHandler.POST_REQUEST_KEY_HEADER]
            event_map = self.json_args[DeviceDataHandler.POST_REQUEST_KEY_EVENT]
            device_store = get_device_store()
            endpointKeyHash = header_map[DeviceDataHandler.POST_REQUEST_KEY_ENDPOINTKEYHASH][DeviceDataHandler.DATA_TYPE_STRING]
            logical_address = device_store.get_logical_address_by_hashkey(endpointKeyHash)
            item_key_values = parse_data(event_map)
        except Exception as e:
            message = "Receive and parse kaa device's data failure: %s" % e.message
            logger.error(message)
            return

        # send data
        device_host_name = logical_address
        for item_key_value in item_key_values:
            item_key = item_key_value["key"]
            item_value = item_key_value["value"]
            val = zabbix_send_data(device_host_name, item_key, item_value)

app = tornado.web.Application([
    (r"^%s/data$" % BASE_URL, DeviceDataHandler),
    ])

class APIService(Thread):
    def __init__(self, host, port):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.running = False

    def run(self):
        logger.info("API service started")
        app.listen(self.port, self.host)
        tornado.ioloop.IOLoop.instance().start()

    def start(self):
        if self.running:
            logger.info("API service is already running")
        else:
            logger.info("Starting API service")
            self.running = True
            Thread.start(self)

    def stop(self):
        self.running = False
        logger.info("Stopping API service")
        tornado.ioloop.IOLoop.instance().stop()
        logger.info("API service stopped")

def test_myhandler():
    import time
    api_service = APIService(config.WEB_SERVICE_HOST, config.WEB_SERVICE_PORT)
    print "Starting API service"
    api_service.start()
    print "API service started"
    time.sleep(80)
    print "Stopping API service"
    api_service.stop()
    print "API service stopped"


if __name__ == "__main__":
    test_myhandler()
