#!/usr/bin/env python
# -*- coding:utf-8 -*-
import socketserver
import subprocess
import logging, logging.config
import urllib3
import json
import socket
import base64
import struct
import math
import http.client
import uuid

logging.config.fileConfig("logging_socket_http.ini")
log = logging.getLogger(__name__)



class ExSocketToHttpServer(socketserver.BaseRequestHandler):
    log.info("========request started==========")

    def handle(self):
        try:
            print("========client started==========")
            log.info("========client started==========")
            print("got connection from", self.client_address)
            conn = self.request
            socket_uuid_id=uuid.uuid4().hex
            while True:
                total_data = None
                total_length = 0
                first_data = conn.recv(1024).strip()
                print("first data for one receive loop:%s" % str(first_data))
                log.info("first data for one receive loop:%s" % str(first_data))
                if len(first_data) < 1:
                    conn.send(first_data)
                    break
                runTimes=0
                while True:
                    runTimes=runTimes+1
                    print("runTimes %s" % str(runTimes))
                    if first_data and not total_data:  # first data from conn is not null and total_data(buffer for received data) is null
                        total_data = first_data  # first data from conn
                        first_data = None  # remove first data after it is added to total data
                    if len(total_data) < 4:  # because the length for whole package is stored in 4 bytes, if the total data is less then 4, system needs to continue receive data from conn
                        data = conn.recv(1024).strip()
                        total_data = total_data + data
                        runTimes=runTimes-1
                        continue
                    if len(total_data) == 4 and total_length == 0:  # total_data length is 4
                        a = struct.unpack('i', total_data)  # get package length from total data
                        total_length = a[0]
                        print("content(without first four bytes) length :%s" % str(total_length))
                        print("first four bytes content:%s" % str(total_data))
                        log.info("first four bytes content:%s" % str(total_data))
                        #                   print("first str length:%d" % total_length)
                    if len( total_data) > 4:  # if total_data length is more than 4, the first time recevied data's length is more than 4, and package length is 0, get length from first four bytes from total data
                        if total_length == 0:  # package length is never set, the first received data length is more then 4
                            print("total_data:%s" % str(total_data))
                            total_length_data = total_data[:4]
                            print("total_length_data:%s" % str(total_length_data))
                            a = struct.unpack('l', total_length_data)
                            total_length = a[0]
                        print("first str length2:%d" % total_length)
                    total_length = total_length + 4  # add first 4 bytes length to get the complete length for whole package
                    if len(total_data) < total_length:
                        left_length = total_length - len(total_data)  # remain data which is needed to be sent
                        print("content_length   :%s" % str(left_length))
                        log.info("content_length   :%s" % str(left_length))
                        times = math.ceil(left_length / 1024)  # calcuate the loop times to receive data from conn
                        print("receive times for content data:%s" % str(times))
                        log.info("receive times for content data:%s" % str(times))
                        remain = total_data
                        for i in range(times):
                            data = conn.recv(1024)
                            if not remain:
                                remain = data
                            else:
                                remain = remain + data
                            print("data str :%s" % str(data))
                            print("data length str :%d" % len(data))
                        print("data length str :%d" % len(remain))
                        log.info("content data length str :%d" % len(remain))
                        log.info("content data str :%s" % str(remain))
                        encoderemain=base64.urlsafe_b64encode(remain)
                        str_encoderemain=str(encoderemain,"utf-8") #at server first convert to base64 then convert to utf-8 string, at clint reverse process

                      #  byte_encoderemain=bytes(str_encoderemain,"utf-8")
                      #  remain=base64.urlsafe_b64decode(byte_encoderemain)
                        http_return_data = self.http_client_get_handle(str_encoderemain,socket_uuid_id)
                        log.info("http return data :%s" % str(http_return_data))
                        print("http return data :%s" % str(http_return_data))
                        print("=============http complete==========")
                        conn.send(http_return_data)
                     #   sk.send(remain)
                        break
                    else:
                        print("send total_data length:%s" % str(len(total_data)))
                        print("send total_length length:%s" % str(total_length + 3))
                        print("send str :%s" % str(total_data))

                        encoderemain=base64.urlsafe_b64encode(total_data)
                        str_encoderemain=str(encoderemain,"utf-8")
                  #      byte_encoderemain=bytes(str_encoderemain,"utf-8")
                 #       remain=base64.urlsafe_b64decode(byte_encoderemain)
                 #       sk.send(remain)
                        http_return_data=self.http_client_get_handle(str_encoderemain,socket_uuid_id)
                        log.info("http return data :%s" % str(http_return_data))
                        print("http return data :%s" % str(http_return_data))
                      #  return_data_raw = base64.urlsafe_b64decode(return_data)
                        print("=============http complete==========")
                        conn.send(http_return_data)
                        break

        except Exception as err:
            print(err)
            log.error(err)
        finally:
            print("========request closed==========")
            log.info("========request closed==========")


    def http_client_get_handle(self,data,session_id):
        http=urllib3.PoolManager()
        r=http.request('GET','http://localhost/jlecdg12net?'+"sessionid="+session_id+"&data="+data,timeout=60.0,retries=False)
        if r.status==200:
            log.info("http.data is%s", 'http://localhost/jlecdg12net?'+"sessionid="+session_id+"&data="+data)
            print("http.data is%s", 'http://localhost/jlecdg12net?'+"sessionid="+session_id+"&data="+data)
            return_raw_data= r.data
         #   return_byte_data=bytes(return_raw_data,"utf-8")
            return_base_data=base64.urlsafe_b64decode(return_raw_data)
            return return_base_data
        print("http.status is%s", str(r.status))
        log.info("http.status is%s", str(r.status))
        return None

if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(('192.168.0.104', 10002), ExSocketToHttpServer)
    print('=========socket server start =============')
    server.serve_forever()
