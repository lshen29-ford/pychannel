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

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)



class ExSocketToHttpServer(socketserver.BaseRequestHandler):
    log.info("========request started==========")

    def handle(self):
        try:
            ip_port = ('139.196.108.194', 12501)
            sk = socket.socket()
            sk.connect(ip_port)
            print("========client started==========")
            log.info("========client started==========")
            print("got connection from", self.client_address)
            conn = self.request
            while True:
                total_data = None
                total_length = 0
                first_data = conn.recv(1024).strip()
                print("first data for one receive loop:%s" % str(first_data))
                log.info("first data for one receive loop:%s" % str(first_data))
                if len(first_data) < 1:
                    conn.send(first_data)
                    break
                while True:
                    if first_data and not total_data:  # first data from conn is not null and total_data(buffer for received data) is null
                        total_data = first_data  # first data from conn
                        first_data = None  # remove first data after it is added to total data
                    if len(
                            total_data) < 4:  # because the length for whole package is stored in 4 bytes, if the total data is less then 4, system needs to continue receive data from conn
                        data = conn.recv(1024).strip()
                        total_data = total_data + data
                        continue
                    if len(total_data) == 4 and total_length == 0:  # total_data length is 4
                        a = struct.unpack('i', total_data)  # get package length from total data
                        total_length = a[0]
                        print("content(without first four bytes) length :%s" % str(total_length))
                        print("first four bytes content:%s" % str(total_data))
                        log.info("first four bytes content:%s" % str(total_data))
                        #                   print("first str length:%d" % total_length)
                    if len(
                            total_data) > 4:  # if total_data length is more than 4, the first time recevied data's length is more than 4, and package length is 0, get length from first four bytes from total data
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
                        a=base64.urlsafe_b64encode(remain)
                        remain=base64.urlsafe_b64decode(a)
                        sk.send(remain)
                        break
                    else:
                        print("send total_data length:%s" % str(len(total_data)))
                        print("send total_length length:%s" % str(total_length + 3))
                        print("send str :%s" % str(total_data))
                        sk.send(total_data)
                        break
                """
                while True:
                    other_server_ack_msg = sk.recv(1024).strip()
                    conn.send(other_server_ack_msg)
                    print("complete other_server_ack_msg:%s" % str(other_server_ack_msg))
                    print("complete length :%d" % len(other_server_ack_msg))
                    log.info("complete other_server_ack_msg:%s" % str(other_server_ack_msg))
                    log.info("complete length :%d" % len(other_server_ack_msg))
                    if len(other_server_ack_msg) < 1:
                        break
                    if len(other_server_ack_msg) > 4:
                        break
                """
        except Exception as err:
            print(err)
            log.error(err)
        finally:
            sk.shutdown(2)
            sk.close()
            print("========client closed==========")
            print("========request closed==========")
            log.info("========client closed==========")
            log.info("========request closed==========")

    def http_client_get_Handle(self):
        conn = http.client.HTTPSConnection("localhost", 80, timeout=10)
        conn.request("GET", "/")
        r1 = conn.getresponse()
        print(r1.status, r1.reason)
        data1 = r1.read()  # This will return entire content.
        return data1
    # The following example demonstrates reading data in chunks.
    #    conn.request("GET", "/")
    #    r1 = conn.getresponse()
    #    while not r1.closed:
    #    print(r1.read(200))

if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(('101.92.170.100', 10002), ExSocketToHttpServer)
    server.serve_forever()