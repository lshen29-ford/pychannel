#!/usr/bin/env python
# -*- coding:utf-8 -*-
import socket
import urllib3
import base64

print ("客户端启动：")
http = urllib3.PoolManager()
r = http.request('GET', 'http://localhost/jlecdg12net', timeout=60.0, retries=False)
if r.status == 201:
    return_raw_data = r.data
    content = base64.urlsafe_b64decode(return_raw_data)
byte=str(content,"utf-8")
print("http.status is %s"% str(r.status))
print("http.content is %s" % byte)