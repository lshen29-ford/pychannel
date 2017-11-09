#!/usr/bin/env python
# -*- coding:utf-8 -*-

import http.server
import socketserver
import socket
import threading
import base64
import logging, logging.config
import time
from urllib.parse import urlparse, parse_qs
import ex_request_handler



logging.config.fileConfig("logging_http_socket.ini")
log = logging.getLogger(__name__)

socket_pool = {}
socket_delay_time=60

class SocketItem():
    session_id = 0
    expire_time = 0
    socket = None

    def __init__(self,session_id,expire_time,socket):
        self.session_id=session_id
        self.expire_time=expire_time
        self.socket=socket

class SocketManager():

    @staticmethod
    def create_store_socket_session(session_id):
        if session_id not in socket_pool.keys():
            socket=create_socket_client()
            socket_item = SocketItem(session_id, time.time() + socket_delay_time, socket)
            socket_pool[session_id] = socket_item
        return socket

    @staticmethod
    def get_socket_sessionid(session_id):
         if session_id in socket_pool.keys():
             return socket_pool[session_id].socket
         return None

    @staticmethod
    def clear_expired_socket():
        print("socket expire time is running %s" % time.time())
     #   logging.info("expire time is running at %s" % time.time())

        expired_session_key=[]
        for item in socket_pool.values():
            expired_session_key.append(item.session_id)
        print("socket pool has %s" % len(expired_session_key))
        logging.info("socket pool has %s" % len(expired_session_key))
        for expired_session_id in expired_session_key:
            if socket_pool[expired_session_id].expire_time<time.time():
                close_socket_client(socket_pool[expired_session_id].socket)
                del socket_pool[expired_session_id]

    @staticmethod
    def start_period_clean():
    #    SocketManager.clear_expired_socket()
        while 1:
            threading.Timer(1, SocketManager.clear_expired_socket).start()
            time.sleep(10)


class HttpToSocketRequestHandler(ex_request_handler.BaseHTTPRequestNoLimitationHandler):




    def set_header_content(self,status_code,ecode_str=None):
        self.send_response(status_code)
        self.send_header("Content-type", "text/html; charset=utf-8")  # 发送html头，这里可说明文件类型和字符集等信息
        if ecode_str:
            print("complete http send length :%d" % len(bytes(ecode_str, encoding="utf-8")))
            self.send_header("Content-Length", str(len(bytes(ecode_str, encoding="utf-8"))))  # 发送html头   说明文件长度 注意，这里如果长度和实际长度不一致的话，后面客户端处理时就会触发IncompleteRead 这个异常。
        self.end_headers()
        if ecode_str:
            self.wfile.write(bytes(ecode_str, encoding="utf-8"))


    def do_GET(self):
        sk=None
        try:
            if 'jlecdg12net' in self.path:
                if '?' in self.path:  # 如果带有参数

                    logging.info("raw path is  %s" % self.path)
                    #querycontent=self.path.split('?', 1)[1]
                    url = self.path
                    o = urlparse(url)
                    query =parse_qs(o.query)
                    if 'data' in query:
                        querycontent= query['data']
                        logging.info("query data is  %s" % querycontent)
                    else:
                        return
                    if 'sessionid' in query:
                        session_id=query['sessionid'][0]
                        logging.info("session id is  %s" % session_id)
                    else:
                        return
                    querycontent_bytes=bytes(querycontent[0],"utf-8")
                    raw_data=base64.urlsafe_b64decode(querycontent_bytes)

                    sk = SocketManager.get_socket_sessionid(session_id)
                    if not sk:
                        sk = SocketManager.create_store_socket_session(session_id)

                    print("received raw_data:%s" % str(raw_data))
                    logging.info("received raw_data:%s" % str(raw_data))
                    if not sk:
                        return
                    sk.send(raw_data)
                    raw_data=None
                    other_server_ack_msg=None
                    while True:
                        other_server_ack_msg = sk.recv(1024).strip()
                        print("complete other_server_ack_msg:%s" % str(other_server_ack_msg))
                        print("complete length :%d" % len(other_server_ack_msg))
                        logging.info("complete other_server_ack_msg:%s" % str(other_server_ack_msg))
                        if len(other_server_ack_msg) < 1:
                            break
                        if len(other_server_ack_msg) > 4:
                            other_server_ack_msg_response=base64.urlsafe_b64encode(other_server_ack_msg)
                            ecode_str=str(other_server_ack_msg_response,"utf-8")
                            break

                    if other_server_ack_msg :
                        self.set_header_content(200, ecode_str)
                    else:
                        self.set_header_content(500)
                        print("500, wrong information,no other_server_ack_msg")
                        logging.info("500, wrong information, no other_server_ack_msg")
                            # name=str(bytes(params['name'][0],'GBK'),'utf-8')
                else:
                    content = "url base is right"
                    self.set_header_content(201,content)
                    logging.info("201, url base is right")
                    print("201, url base is right")
            else:
                self.set_header_content(202, "started, url base is not right")
                print("202 started, url base is not right")
                logging.info("202 started, url base is not right")
        except Exception as err:
            print(err)
            log.error(err)
        finally:
            print("===============request is closed==============")
            logging.info("===============request is closed==============")
            #if sk:
            #   self.close_socket_client(sk)


    def do_POST(self):
        to_do=None
    #   self.process(2)


def create_socket_client():
    ip_port = ('139.196.108.194', 12501)
    sk = socket.socket()
    sk.connect(ip_port)
    return sk


def close_socket_client(sk):
    sk.shutdown(2)
    sk.close()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""

def run(server_class=ThreadedHTTPServer, handler_class=HttpToSocketRequestHandler):
    server_address = ('localhost', 80)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ == '__main__':
    t = threading.Thread(target=SocketManager.start_period_clean, args=())
    t.start()
    run()

