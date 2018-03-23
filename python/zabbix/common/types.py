#coding: utf-8
from zabbix.common.utils import gen_letter_label
from zabbix.common.definitions import (EMAIL_MEDIATYPE_ID,
                                       SMS_MEDIATYPE_ID,
                                       RECEIVE_NOTIFICATION_ALL_PERIOD,
                                       RECEIVE_NOTIFICATION_ALL_SEVERITY,
                                       NOTIFICATION_MODE_ALL,
                                       NOTIFICATION_MODE_SMS,
                                       NOTIFICATION_MODE_EMAIL)

NOTIFICATION_SUBJECT = "设备【{HOST.NAME}】发生异常"
NOTIFICATION_MESSAGE = "【贞泉】尊敬的用户您好，您的设备编号[{HOST.NAME}] 发生异常：{TRIGGER.NAME}，当前值：{ITEM.LASTVALUE}，严重程度：{TRIGGER.SEVERITY}，事件编号：{EVENT.ID}，请知悉，谢谢!"

def pack_usermedias(smss, emails):
    medias = []
    for sms in smss:
        media={"mediatypeid": SMS_MEDIATYPE_ID,
                "sendto": sms,
                "active": 0,
                "severity": RECEIVE_NOTIFICATION_ALL_SEVERITY,
                "period": RECEIVE_NOTIFICATION_ALL_PERIOD}
        medias.append(media)

    for email in emails:
        media={"mediatypeid": EMAIL_MEDIATYPE_ID,
                "sendto": email,
                "active": 0,
                "severity": RECEIVE_NOTIFICATION_ALL_SEVERITY,
                "period": RECEIVE_NOTIFICATION_ALL_PERIOD}
        medias.append(media)
    return medias

def pack_action_conditions(host_ids, item_name, old_conditions):
    """
    Pack host_ids and item_name to old_conditions

    Input:
      * item_name: monitoring item name
      * host_ids: host id list
      * old_conditions: old condition list
    Output:
      * conditions: condition list
    """
    conditions = []
    if isinstance(old_conditions, list):
        conditions = old_conditions
    if isinstance(host_ids, list):
        for host_id in host_ids:
            condition={"conditiontype": "1","operator": "0","value": host_id}
            conditions.append(condition)
    if item_name != None and item_name.strip() != "":
        condition={"conditiontype": "3","operator": "2","value": item_name}
        conditions.append(condition)
    return conditions

def remove_action_conditions(host_id, old_conditions):
    """
    Remove host_id from old_conditions

    Input:
      * host_id: host id
      * old_conditions: old condition list
    Output:
      * conditions: condition list
    """
    conditions = []
    if isinstance(old_conditions, list):
        conditions = old_conditions
    if host_id != None:
        for condition in conditions:
            if condition["conditiontype"]=="1" and condition["operator"]=="0" \
                    and condition["value"]==host_id:
                conditions.remove(condition)
    return conditions

def pack_action_operations(userid, notification_mode=NOTIFICATION_MODE_SMS):
    """
    Pack action operations by userid and notification_mode

    Input:
      * user_id: the user id
      * notification_mode: default NOTIFICATION_MODE_ALL, other:NOTIFICATION_MODE_EMAIL, NOTIFICATION_MODE_SMS
    Output:
      * operations: operation list
    """
    def pack_email(userid):
        email={"operationtype": 0,
                "esc_period": 0,
                "esc_step_from": 1,
                "esc_step_to": 1,
                "evaltype": 0,
                "opmessage_grp": [],
                "opmessage_usr": [{"userid": userid}],
                "opmessage": {"default_msg": 1,
                    "mediatypeid": EMAIL_MEDIATYPE_ID}}
        return email

    def pack_sms(userid):
        sms={"operationtype": 0,
                "esc_period": 0,
                "esc_step_from": 1,
                "esc_step_to": 1,
                "evaltype": 0,
                "opmessage_grp": [],
                "opmessage_usr": [{"userid": userid}],
                "opmessage": {"default_msg": 1,
                    "mediatypeid": SMS_MEDIATYPE_ID}}
        return sms

    operations = []
    if notification_mode == NOTIFICATION_MODE_ALL:
        operations.append(pack_email(userid))
        operations.append(pack_sms(userid))
    elif notification_mode == NOTIFICATION_MODE_EMAIL:
        operations.append(pack_email(userid))
    elif notification_mode == NOTIFICATION_MODE_SMS:
        operations.append(pack_sms(userid))

    return operations

def gen_action_condition_formulaid(num):
    """
    Input:
    * num: a digit
    Output:
    * formula_id: the formula id of action condition, for example: A or B or AB
    """
    formula_id = ""
    formula_id = gen_letter_label(formula_id ,num)
    return formula_id
