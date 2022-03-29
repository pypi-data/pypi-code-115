#!/bin/python
######      IMPORTANT  FOR OPCUA        #####
# GENERATE A PRIVATE KEY AND A CERTIF WITH COMMAND
## openssl req -x509 -newkey rsa:4096 -keyout <key.pem> -out <cert.pem> -days 7200 -nodes
## or take an existing certif/key pair
# do not forget to change pg_hba.conf and restart server +
# change password of uer postgres with :
# alter user <postgres> password '<newpassword>';

import importlib
import os
import dorianUtils.comUtils as comUtils
import time,datetime as dt,sys
importlib.reload(comUtils)
import smallPowerDash.smallPower as smallPower
importlib.reload(smallPower)
start=time.time()
dumperSmallPower = smallPower.SmallPower_dumper()
dumperSmallPower.dbTable='test_realtimedata'
# dumperSmallPower.park_database()
dumperSmallPower.start_dumping()
