EMAIL_MEDIATYPE_ID = "1"
SMS_MEDIATYPE_ID = "4"

RECEIVE_NOTIFICATION_ALL_PERIOD = "1-7,00:00-24:00"

"""
Severity: this value is stored as a binary number,  from left to right in turn represent "severity" is:
    [not classified] [information] [warning] [average] [high] [disaster]
    For example: binary '1100' equal to 12 , it means that its severity is: warning and average
                 binary '111111' is equal to 63 , it means that its severity is: all
"""
RECEIVE_NOTIFICATION_ALL_SEVERITY = 63

NOTIFICATION_MODE_INVALID = 0
NOTIFICATION_MODE_EMAIL = 1
NOTIFICATION_MODE_SMS = 2
NOTIFICATION_MODE_ALL = 3
