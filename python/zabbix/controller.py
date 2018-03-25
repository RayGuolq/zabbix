import requests
import json
from threading import Lock

import zabbix.config as zabbix_config
from zabbix.exception import ZabbixException
from zabbix.common.utils import get_logger, random_chars
from zabbix.common.types import (pack_usermedias,
                                 pack_action_conditions,
                                 remove_action_conditions,
                                 pack_action_operations,
                                 NOTIFICATION_SUBJECT,
                                 NOTIFICATION_MESSAGE)
from zabbix.common.definitions import NOTIFICATION_MODE_SMS

logger = get_logger()

ZABBIX_HTTP_SUCCESS = 200
ZABBIX_RESPONSE_KEY_ERROR = "error"
ZABBIX_RESPONSE_KEY_RESULT = "result"


zabbix_controller = None
zabbix_lock = Lock()

def get_zabbix_controller():
    logger.debug("Get zabbix controller")
    zabbix_lock.acquire()
    global zabbix_controller
    if zabbix_controller is not None:
        zabbix_lock.release()
        logger.debug("Zabbix controller successfully get")
        return zabbix_controller
    try:
        zabbix_controller = ZabbixController(zabbix_config.ZABBIX_USER,
                         zabbix_config.ZABBIX_PASSWORD)
        logger.debug("Zabbix controller successfully get")
    except Exception as e:
        logger.error("Initialize zabbix controller failed: %s" % e.message)
    zabbix_lock.release()
    return zabbix_controller

class ZabbixController:
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.auth = self.get_auth()

    def get_auth(self):
        """
        Get auth:
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "user.login","params": {"user": "Admin","password": "zabbix"},"id": 1,"auth": null}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php;
        Return:
          {"jsonrpc":"2.0","result":"8725a8b9977280d879b2bf7449160064","id":1}
        """
        request_method = "user.login"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"user": self.user,
                    "password": self.password},
                "id": 1,
                "auth": None}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix get auth info failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix get auth info failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix get auth info failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result

    def get_template_id(self, template_name):
        """
        Get template id by template name:
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "template.get","params": {"output": ["templateid"],"filter": {"host": ["Tahoe device template"]}},"auth": "8725a8b9977280d879b2bf7449160064","id": 1}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php;
        Return:
          {"jsonrpc":"2.0","result":[{"templateid":"10105"}],"id":1}

        Input:
          * template_name: template name
        Output:
          * template_id: template id
        """
        request_method = "template.get"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"output":["templateid"],
                    "filter": {"host":[template_name]}},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix set template id failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix set template id failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix set template id failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result[0]["templateid"]

    def get_hostgroup_id(self, hostgroup_name):
        """
        Get host group id by host group name:
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "hostgroup.get","params": {"output": "extend","filter": {"name": ["tahoe devices"]}},"auth": "8725a8b9977280d879b2bf7449160064","id": 1}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php;
        Return:
          {"jsonrpc":"2.0","result":[{"groupid":"8","name":"tahoe devices","internal":"0","flags":"0"}],"id":1}

        Input:
          * hostgroup_name: hostgroup name
        Output:
          * hostgroup_id: hostgroup id
        """
        request_method = "hostgroup.get"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"output":"extend",
                    "filter": {"name":[hostgroup_name]}},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix set host group id failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix set host group id failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix set host group id failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result[0]["groupid"]

    def get_usergroup_id(self, usergroup_name):
        """
        Get host group id by user group name:
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "usergroup.get","params": {"output": "extend", "filter":{"name": ["tahoe users"]}},"auth": "8725a8b9977280d879b2bf7449160064","id": 1}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php;
        Return:
          {"jsonrpc":"2.0","result":[{"usrgrpid":"13","name":"tahoe users","gui_access":"0","users_status":"0","debug_mode":"0"}],"id":1}

        Input:
          * usergroup_name: usergroup name
        Output:
          * usergroup_id: usergroup id
        """
        request_method = "usergroup.get"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"output":"extend",
                    "filter": {"name":[usergroup_name]}},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix set host group id failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix set host group id failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix set host group id failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result[0]["usrgrpid"]

    def get_userinfo_by_name(self, username):
        """
        Get user info by username:
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "user.get","params": {"output": "extend","selectMedias": "extend", "filter": {"alias": ["guoleiqiang"]}},"auth": "8725a8b9977280d879b2bf7449160064","id": 1}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php;
        Return:
          {"jsonrpc":"2.0","result":[{"userid":"3","alias":"guoleiqiang","name":"New","surname":"User","url":"","autologin":"1","autologout":"0", "lang":"en_GB","refresh":"30","type":"1","theme":"default","attempt_failed":"0","attempt_ip":"","attempt_clock":"0","rows_per_page":"50", "medias":[{"mediaid":"1","userid":"3","mediatypeid":"1","sendto":"guoleiqiang@iwaterdata.com","active":"0","severity":"63","period":"1-7,00:00-24:00"}]}],"id":1}

        Input:
          * username: user login name
        Output:
          * userinfo: dict
            ** userid : user id
            ** alias : user login name
            ** medias : list, meanning SMS, E-mail and other contact information
            ......
        """
        request_method = "user.get"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"output":"extend",
                    "selectMedias":"extend",
                    "filter": {"alias":[username]}},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix get user info by username failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix get user info by username failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix get user info by username failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        user = None
        if len(result) > 0:
            user = result[0]
        return user

    def create_user(self, username, user_group_id, smss=[], emails=[]):
        """
        Create user:
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "user.create","params": [{"alias": "John","passwd": "John","usrgrps": [{"usrgrpid": "13"}],"user_medias": [{"mediatypeid": "1","sendto": "John@company.com","active": 0,"severity": 63,"period": "1-7,00:00-24:00"}]}],"auth": "8725a8b9977280d879b2bf7449160064","id":1}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php; 
        Return:
          {"jsonrpc":"2.0","result":{"userids":["5"]},"id":1}

        Input:
          * username: user login name
          * user_group_id: user group id
          * smss: sms list
          * emails: emails list
        Output:
          * userid : user id
        """
        request_method = "user.create"
        medias = pack_usermedias(smss, emails)
        password = random_chars(6)
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"alias": username,
                    "passwd": password,
                    "usrgrps": [{"usrgrpid": user_group_id}],
                    "user_medias": medias},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix create user failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix create user failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix create user failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result["userids"][0]

    def update_user_medias(self, user_id, smss=[], emails=[]):
        """
        Update user medias:
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "user.updatemedia","params": {"users": [{"userid": "4"}],"medias": [{"mediatypeid": "1","sendto": "support@company.com","active": 0,"severity": 63,"period": "1-7,00:00-24:00"}]},"auth": "8725a8b9977280d879b2bf7449160064","id": 1}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php;
        Return:
          {"jsonrpc":"2.0","result":{"userids":[4]},"id":1}

        Input:
          * user_id: user id
        Output:
          * user_id: user id
        """
        request_method = "user.updatemedia"
        medias = pack_usermedias(smss, emails)

        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"users": [{"userid": user_id}],
                    "medias": medias},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix update user medias failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix update user medias failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix update user medias failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result["userids"][0]

    def create_host(self, host_name, host_group_id, host_template_id):
        """
        Create host:
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "host.create","params": [{"host": "tahoe device4","interfaces": [{"type": 1,"main": 1,"useip": 1,"ip": "127.0.0.1","dns": "","port": "10050"}],"groups": [{"groupid": "8"}],"templates": [{"templateid": "10105"}],"inventory_mode": 0,"inventory": {"macaddress_a": "ab:3c:6d:5c"}}],"auth": "8725a8b9977280d879b2bf7449160064","id": 1}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php;
        Return:
          {"jsonrpc":"2.0","result":{"hostids":["10112"]},"id":1}

        Input:
          * host_name: host name
          * host_group_id: host group id
          * host_template_id: host template id
        Output:
          * host_id: created host id
        """
        request_method = "host.create"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": [{"host": host_name,
                    "interfaces": [{"type": 1,
                        "main": 1,
                        "useip": 1,
                        "ip": "127.0.0.1",
                        "dns": "",
                        "port":"10050"}],
                    "groups": [{"groupid": host_group_id}],
                    "templates": [{"templateid": host_template_id}]}],
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix create host failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix create host failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix create host failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result["hostids"][0]

    def delete_hosts(self, host_ids):
        """
        Delete hosts by host_ids.

        Input:
          * host_ids: host id list
        Output:
          * host_id: deleted host ids
        """
        request_method = "host.delete"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": host_ids,
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix delete host failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix delete host failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix delete host failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result["hostids"]

    def get_hosts(self, host_names):
        """
        Get hosts by host names
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "host.get","params": {"output": "extend", "filter": {"host": ["tahoe device4"]}},"auth": "8725a8b9977280d879b2bf7449160064","id": 1}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php;
        Return:
          {"jsonrpc":"2.0","result":[{"hostid":"10112","proxy_hostid":"0","host":"tahoe device4", "status":"0","disable_until":"0","error":"","available":"0","errors_from":"0","lastaccess":"0","ipmi_authtype":"0","ipmi_privilege":"2","ipmi_username":"","ipmi_password":"","ipmi_disable_until":"0","ipmi_available":"0","snmp_disable_until":"0","snmp_available":"0", "maintenanceid":"0","maintenance_status":"0","maintenance_type":"0","maintenance_from":"0","ipmi_errors_from":"0", "snmp_errors_from":"0","ipmi_error":"","snmp_error":"","jmx_disable_until":"0","jmx_available":"0","jmx_errors_from":"0","jmx_error":"", "name":"tahoe device4","flags":"0","templateid":"0","description":"","tls_connect":"1","tls_accept":"1","tls_issuer":"", "tls_subject":"", "tls_psk_identity":"","tls_psk":""}],"id":1}

        Input:
          * host_names: a list host name
        Output:
          * hosts: a list of host info
          ** hostinfo: a dict
          *** hostid: host id
          *** host: host name
          *** name: host name
          ......
        """
        request_method = "host.get"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"output":"extend",
                    "filter": {"host":host_names}},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix get hosts by host names failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix get hosts by host names failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix get hosts by host names failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        hosts = None
        if len(result) > 0:
            hosts = result
        return hosts

    def create_action(self, item_name, host_ids, user_name, user_id, notification_mode=NOTIFICATION_MODE_SMS):
        """
        Input:
          * item_name: monitoring item name
          * host_ids: host id list
          * user_name: the user name
          * user_id: the user id
          * notification_mode: default NOTIFICATION_MODE_ALL, other:NOTIFICATION_MODE_EMAIL, NOTIFICATION_MODE_SMS
        Output:
          * actionid: created action id
        """
        action_name = "%s`s device occur %s exception action" % (user_name, item_name)
        conditions = pack_action_conditions(host_ids, item_name, None)
        operations = pack_action_operations(user_id, notification_mode)
        request_method = "action.create"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": [{"name": action_name,
                    "eventsource": 0,
                    "status": 0,
                    "esc_period": 120,
                    "def_shortdata": NOTIFICATION_SUBJECT,
                    "def_longdata": NOTIFICATION_MESSAGE,
                    "filter": {"evaltype": "0",
                        "conditions": conditions},
                    "operations": operations}],
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix create action failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix create action failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix create action failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result["actionids"][0]

    def delete_actions(self, action_ids):
        """
        Delete actions by action_ids

        Input:
          * action_ids: action id list
        Output:
          * action_ids: deleted action ids
        """
        request_method = "action.delete"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": action_ids,
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix delete action failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix delete action failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix delete action failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result["actionids"]

    def get_actions_by_userid(self, user_id):
        """
        Get actions by user id:
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "action.get","params": {"output": "extend","selectOperations": "extend","selectRecoveryOperations": "extend","selectFilter": "extend","userids": ["3"],"filter": {"eventsource": 0}},"auth": "8725a8b9977280d879b2bf7449160064","id": 1}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php;
        Return:
          {"jsonrpc":"2.0","result":[{"actionid":"13","name":"guoleiqiang`s tahoe device tds too high","eventsource":"0","status":"0","esc_period":"120","def_shortdata":"{TRIGGER.NAME}: {TRIGGER.STATUS}","def_longdata":"{TRIGGER.NAME}: {TRIGGER.STATUS}\r\nLast value: {ITEM.LASTVALUE}\r\n\r\n{TRIGGER.URL}\r\n\r\nOriginal event ID: {EVENT.ID}","r_shortdata":"","r_longdata":"","maintenance_mode":"1","filter":{"evaltype":"3","formula":"A and (B or C)","conditions":[{"conditiontype":"3","operator":"2","value":"tds","value2":"","formulaid":"A"},{"conditiontype":"3","operator":"2","value":"tahoe device3","value2":"","formulaid":"B"},{"conditiontype":"3","operator":"2","value":"tahoe device5","value2":"","formulaid":"C"}],"eval_formula":"A and (B or C)"},"operations":[{"operationid":"23","actionid":"13","operationtype":"0","esc_period":"0","esc_step_from":"1","esc_step_to":"1","evaltype":"0","recovery":"0","opconditions":[],"opmessage":{"operationid":"23","default_msg":"0","subject":"{TRIGGER.NAME}: {TRIGGER.STATUS}","message":"\u3010\u8d1e\u6cc9\u3011\u95ee\u9898\uff1a{TRIGGER.NAME}\uff0c\u5f53\u524d\u503c\uff1a {ITEM.LASTVALUE}\uff0c\u4e8b\u4ef6\u7f16\u53f7\uff1a{EVENT.ID}\uff0c\u8bf7\u77e5\u6089\uff0c\u8c22\u8c22","mediatypeid":"4"},"opmessage_grp":[],"opmessage_usr":[{"operationid":"23","userid":"3"}]}],"recoveryOperations":[]}],"id":1}

        Input:
          * user_id: user id
        Output:
          * actions: is a list of action json format
        """
        request_method = "action.get"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"output":"extend",
                    "selectOperations":"extend",
                    "selectRecoveryOperations":"extend",
                    "selectFilter":"extend",
                    "userids": [user_id],
                    "filter": {"eventsource": 0}},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix get actions by user id failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix get actions by user id failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix get actions by user id failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result

    def get_actions_by_hostid(self, host_id):
        """
        Get actions by host id:
          curl -v -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0","method": "action.get","params": {"output": "extend","selectOperations": "extend","selectRecoveryOperations": "extend","selectFilter": "extend","hostids": ["10113"],"filter": {"eventsource": 0}},"auth": "8725a8b9977280d879b2bf7449160064","id": 1}' http://192.10.0.60:8000/zabbix/api_jsonrpc.php;
        Return:
          {"jsonrpc":"2.0","result":[{"actionid":"13","name":"guoleiqiang`s tahoe device tds too high","eventsource":"0","status":"0","esc_period":"120","def_shortdata":"{TRIGGER.NAME}: {TRIGGER.STATUS}","def_longdata":"{TRIGGER.NAME}: {TRIGGER.STATUS}\r\nLast value: {ITEM.LASTVALUE}\r\n\r\n{TRIGGER.URL}\r\n\r\nOriginal event ID: {EVENT.ID}","r_shortdata":"","r_longdata":"","maintenance_mode":"1","filter":{"evaltype":"3","formula":"A and (B or C)","conditions":[{"conditiontype":"3","operator":"2","value":"tds","value2":"","formulaid":"A"},{"conditiontype":"3","operator":"2","value":"tahoe device3","value2":"","formulaid":"B"},{"conditiontype":"3","operator":"2","value":"tahoe device5","value2":"","formulaid":"C"}],"eval_formula":"A and (B or C)"},"operations":[{"operationid":"23","actionid":"13","operationtype":"0","esc_period":"0","esc_step_from":"1","esc_step_to":"1","evaltype":"0","recovery":"0","opconditions":[],"opmessage":{"operationid":"23","default_msg":"0","subject":"{TRIGGER.NAME}: {TRIGGER.STATUS}","message":"\u3010\u8d1e\u6cc9\u3011\u95ee\u9898\uff1a{TRIGGER.NAME}\uff0c\u5f53\u524d\u503c\uff1a {ITEM.LASTVALUE}\uff0c\u4e8b\u4ef6\u7f16\u53f7\uff1a{EVENT.ID}\uff0c\u8bf7\u77e5\u6089\uff0c\u8c22\u8c22","mediatypeid":"4"},"opmessage_grp":[],"opmessage_usr":[{"operationid":"23","userid":"3"}]}],"recoveryOperations":[]}],"id":1}

        Input:
          * user_id: user id
        Output:
          * actions: is a list of action json format
        """
        request_method = "action.get"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"output":"extend",
                    "selectOperations":"extend",
                    "selectRecoveryOperations":"extend",
                    "selectFilter":"extend",
                    "hostids": [host_id],
                    "filter": {"eventsource": 0}},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix get actions by host id failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix get actions by host id failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix get actions by host id failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result

    def update_action_condition(self, action_id, conditions):
        """
        Update action condition.

        Input:
          * action_id: action id
          * conditions: the conditions is list of update action need to send
        Output:
          * actionid: created action id
        """
        request_method = "action.update"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"actionid": action_id,
                    "filter": {"evaltype": "0",
                        "conditions": conditions}},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix update action condition failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix update action condition failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix update action condition failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result["actionids"][0]

    def update_action_operation(self, action_id, operations):
        """
        Update action operation.

        Input:
          * action_id: action id
          * operations: the operations is list of update action need to send
        Output:
          * actionid: created action id
        """
        request_method = "action.update"
        data = {"jsonrpc": zabbix_config.ZABBIX_JSONRPC_VERSION,
                "method": request_method,
                "params": {"actionid": action_id,
                    "operations": operations},
                "id": 1,
                "auth": self.auth}
        headers = {'Content-Type':'application/json'}
        try:
            rsp = requests.post(zabbix_config.ZABBIX_URL,
                                headers=headers,
                                json=data)
        except Exception as e:
            logger.error("zabbix update action operation failure: %s" % e.message)
            raise
        if rsp.status_code != ZABBIX_HTTP_SUCCESS:
            logger.error("zabbix update action operation failure: code(%d), "
                    "reason: %s" % (rsp.status_code, rsp.reason))
            raise ZabbixException(rsp.reason)
        if rsp.json().has_key(ZABBIX_RESPONSE_KEY_ERROR):
            error = rsp.json()[ZABBIX_RESPONSE_KEY_ERROR]
            reason = error['message'] + " " + error['data']
            logger.error("zabbix update action operation failure: code(%d), "
                    "reason: %s" % (error['code'], reason))
            raise ZabbixException(reason)

        result = rsp.json()[ZABBIX_RESPONSE_KEY_RESULT]
        return result["actionids"][0]

    def get_device_controller(self):
        """
        Get tahoe device controller

        Input:
          N/A
        Output:
          * EndpointController
        """
        return TahoeDeviceController(self)


class TahoeDeviceController:
    MONITORING_ITEMS = ["tds", "running status", "water purified value", \
            "filter1 used","filter2 used", "filter3 used", "filter4 used", "filter5 used", \
            "cold water temperature", "hot water temperature"]

    def __init__(self, zabbix_controller):
        self.zabbix_controller = zabbix_controller
        try:
            self.host_group_id = self.zabbix_controller.get_hostgroup_id(zabbix_config.ZABBIX_HOSTGROUP_NAME)
            self.host_template_id = self.zabbix_controller.get_template_id(zabbix_config.ZABBIX_TEMPLATE_NAME)
            self.user_group_id = self.zabbix_controller.get_usergroup_id(zabbix_config.ZABBIX_USERGROUP_NAME)
        except Exception as e:
            logger.error("Tahoe device controller initialization failure: %s" % e.message)
            raise
        logger.info("Tahoe device controller initialization success")

    def device_first_setup(self, logical_address, username, smss, emails):
        """
        1. create host by device logical address, return host_id
        2. get user info by username
        3. if user is None, create user by username, smss, emails, return user info
           if user, update user medias by user_id, smss, emails
        4. get actions by userid
        5. traversal monitoring items
           if action(Corresponding to the item) is None, create action conditions need host_id, and operations need user_id
           if action(Corresponding to the item), update action conditions to add host_id

        Input:
          * logical_address: device logical address used as a host name
          * username: user login name
          * smss: is a list of user sms
          * emails: is a list of user email
        Output:
          * (status, message): tuple
          ** status: the execution status. bool
          ** message: the failure message on failure
        """
        if not (logical_address != None and logical_address.strip()!="" and \
                username != None and username.strip()!="" and \
                isinstance(smss, list) and isinstance(emails, list)):
            message = "Input parameters format is wrong"
            logger.error("zabbix device first setup failure: %s" % message)
            return (False, message)

        ret = (True, "succeed")
        try:
            logger.info("Get host by logical_address[%s]." % logical_address)
            hosts = self.zabbix_controller.get_hosts([logical_address])
            if hosts != None and len(hosts) > 0:
                message = "host[%s] already existing." % logical_address
                logger.error("zabbix device first setup failure: %s" % message)
                return (False, message)

            logger.info("Create host[%s]." % logical_address)
            host_id = self.zabbix_controller.create_host(logical_address, self.host_group_id, self.host_template_id)
            if not host_id:
                ret = (False, "create device host Failure")
            else:
                logger.info("Get user info by name[%s]." % username)
                user = self.zabbix_controller.get_userinfo_by_name(username)
                if user:
                    user_id = user["userid"]
                    logger.info("Update user medias by user_id[%s]." % user_id)
                    self.zabbix_controller.update_user_medias(user_id, smss, emails)
                else:
                    logger.info("Create user by username[%s], user_group_id[%s]." % (username, self.user_group_id))
                    user_id = self.zabbix_controller.create_user(username, self.user_group_id, smss, emails)
                if not user_id:
                    ret = (False, "create user Failure")
                else:
                    host_ids = [host_id]
                    logger.info("Get actions by user_id[%s]." % user_id)
                    actions = self.zabbix_controller.get_actions_by_userid(user_id)
                    if not actions:
                        for item in TahoeDeviceController.MONITORING_ITEMS:
                            logger.info("Create action by monitoring item[%s], username[%s]." % (item, username))
                            self.zabbix_controller.create_action(item, host_ids, username, user_id)
                    else:
                        for item in TahoeDeviceController.MONITORING_ITEMS:
                            flag = False
                            for action in actions:
                                if item in action["name"]:
                                    # update action conditions to add host_name
                                    old_coditions = action["filter"]["conditions"]
                                    conditions = pack_action_conditions(host_ids, None, old_coditions)
                                    logger.info("Update action, action name[%s]." % action["name"])
                                    self.zabbix_controller.update_action_condition(action["actionid"], conditions)
                                    flag = True
                                    break
                            if not flag:
                                # create action
                                logger.info("Create action by monitoring item[%s], username[%s]." % (item, username))
                                self.zabbix_controller.create_action(item, host_ids, username, user_id)
        except Exception as e:
            message = "zabbix device first setup failure: %s" % e.message
            logger.error(message)
            ret = (False, message)
        return ret

    def remove_device_host(self, logical_address):
        """
        1. get host by device logical address, return host
        2. if host is None, return function
        3. get actions by host id
        4. traversal actions
           if action(Corresponding to the item), update action conditions to remove host_id
           if after the remove host_id, action conditions only remain item_name filter, remove item_name
        5. delete host by host id

        Input:
          * logical_address: device logical address used as a host name
        Output:
          * (status, message): tuple
          ** status: the execution status. bool
          ** message: the failure message on failure
        """
        if logical_address == None and logical_address.strip() == "":
            message = "Input parameters format is wrong"
            logger.error("zabbix remove device host failure: %s" % message)
            return (False, message)

        ret = (True, "succeed")
        try:
            logger.info("Get host by logical_address[%s]." % logical_address)
            hosts = self.zabbix_controller.get_hosts([logical_address])
            if hosts == None or len(hosts) == 0:
                message = "host[%s] not existing." % logical_address
                logger.error("zabbix remove device host failure: %s" % message)
                return (False, message)

            host_id = hosts[0]["hostid"]
            logger.info("Get actions by host_id[%s]." % host_id)
            actions = self.zabbix_controller.get_actions_by_hostid(host_id)
            if actions:
                for action in actions:
                    # update action conditions to remove host_id
                    old_coditions = action["filter"]["conditions"]
                    conditions = remove_action_conditions(host_id, old_coditions)
                    if len(conditions) == 0 or (len(conditions) == 1 and \
                            conditions[0]["conditiontype"]=="3" and conditions[0]["operator"]=="2"):
                        #remove this action by action_id
                        action_id = action["actionid"]
                        logger.info("Remove action[%s] by action_id[%s]." % (action["name"], action_id))
                        self.zabbix_controller.delete_actions([action_id])
                    else:
                        #update action by action_id
                        logger.info("Update action, action name[%s]." % action["name"])
                        self.zabbix_controller.update_action_condition(action["actionid"], conditions)
            #remove host by host id
            logger.info("Remove host by host_id[%s]." % host_id)
            self.zabbix_controller.delete_hosts([host_id])

        except Exception as e:
            message = "zabbix remove device host failure: %s" % e.message
            logger.error(message)
            ret = (False, message)
        return ret

    def update_event_notification(self, host_names, username, smss, emails):
        """
        when through the page setup.
        1. get user info by username
        2. if user is None, create user by username, smss, emails, return user info
           if user, update user medias by user_id, smss, emails
        3. get actions by userid
        4. traversal monitoring items
           if action(Corresponding to the item) is None, create action conditions need host_ids, and operations need user_id
           if action(Corresponding to the item), update action operations to whether notification user_id
        """
        pass



if __name__ == "__main__":
    zabbix_controller = get_zabbix_controller()
    device_controller = zabbix_controller.get_device_controller()
    print "zabbix auth: %s" % zabbix_controller.auth
    print "device host group id: %s" % device_controller.host_group_id
    print "device host template id: %s" % device_controller.host_template_id
    print "device user group id: %s" % device_controller.user_group_id
    logical_address = "DID-20161010010010488a8f7f"
    username = "dealer"
    smss = ["18616764280"]
    emails = ["guoleiqiang@iwaterdata.com"]
    print device_controller.device_first_setup(logical_address, username, smss, emails)
    #print device_controller.remove_device_host(logical_address)
