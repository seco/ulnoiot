# This is based on https://github.com/cpopp/MicroTelnetServer
#
# Major modifications started by ulno (http://ulno.net) on 2017-09-15
# adding chacha encryption

MAGIC = b"UlnoIOT-NetREPL:"

import socket
import network
import uos
import errno
import chacha
import time

last_client_socket = None
server_socket = None


# def decrypt_receive(socket,length=1,timeoutms=None):
#     global _cc_in
#     start_t = time.ticks_ms()
#     answer=bytearray(length)
#     readbytes = 0
#     while readbytes<length:
#         try:
#             answer[readbytes]=_cc_in.decrypt(socket.recv(1))[0]
#             readbytes += 1
#         except (IndexError, OSError) as e:
#             if type(e) == IndexError or len(e.args) > 0 and e.args[0] == errno.EAGAIN:
#                 pass # try eventually again
#             else:
#                 raise
#         if timeoutms is not None \
#                 and time.ticks_diff(time.ticks_ms(),start_t) >= timeoutms:
#             break
#     return answer[0:readbytes]


# Provide necessary functions for dupterm and replace telnet control characters that come in.
class TelnetWrapper():
    def __init__(self, cc_in, cc_out):
        self.cc_in = cc_in
        self.cc_out = cc_out
        self.discard_count = 0
        self.buffer=bytes(0)
        
    def readinto(self, b):
        lb=len(b)
        if lb == 0: return None
        if len(self.buffer) == 0:
            self.buffer = self.cc_in.receive()
 #           print("+",self.buffer,b)
        lbuffer = len(self.buffer)
        if lbuffer == 0: return None
        #if lbuffer == 0: return 0 # this aborts

        #self.buffer=bytes(0)
        #return None

        if lbuffer > 0:
            b[0] = self.buffer[0]
            self.buffer=self.buffer[1:]
#            print("!", b, lb)
            if lbuffer>1: return 1
        return None

        # if lbuffer>lb:
        #     for i in range(lb):
        #         b[i]=self.buffer[i]
        #     self.buffer=self.buffer[lb:]
        # else:
        #     for i in range(lbuffer):
        #         b[i]=self.buffer[i]
        #     self.buffer=bytes(0)
        # print("!",b,lb)
        # return lb

            # readbytes = 0
        # for i in range(len(b)):
        #     try:
        #         byte = 0
        #         # discard telnet control characters and
        #         # null bytes
        #         while (byte == 0):
        #             if len(self.buffer) == 0:
        #                 self.buffer = self.cc_in.receive()
        #             #print("Buffer:", self.buffer)
        #             byte = self.buffer[0]
        #             self.buffer = self.buffer[1:]
        #             if byte == 0xFF:
        #                 self.discard_count = 2
        #                 byte = 0
        #             elif self.discard_count > 0:
        #                 self.discard_count -= 1
        #                 byte = 0
        #
        #         b[i] = byte
        #
        #         readbytes += 1
        #     except (IndexError, OSError) as e:
        #         if type(e) == IndexError or len(e.args) > 0 and \
        #                         e.args[0] == errno.EAGAIN:
        #             if readbytes == 0:
        #                 return None
        #             else:
        #                 return readbytes
        #         else:
        #             raise
        #
        # if readbytes == 0:
        #     return None
        #
        # return readbytes


    def write(self, data):
        self.cc_out.send(data)
        #pass

    def close(self):
        self.cc_in.socket.close()

# Attach new clients to dupterm and 
# send telnet control characters to disable line mode
# and stop local echoing
def accept_telnet_connect(telnet_server):
    global last_client_socket, _key
    
    if last_client_socket:
        # close any previous clients
        uos.dupterm(None)
        last_client_socket.close()
    
    last_client_socket, remote_addr = telnet_server.accept()
    print("Telnet connection from:", remote_addr)

    # reset encryption status vector TODO: consider variable iv
    cc_in = chacha.ChaCha(_key,bytes(8),socket=last_client_socket)

    # prepare answer channel
    last_client_socket.setblocking(False)
    last_client_socket.setsockopt(socket.SOL_SOCKET, 20, uos.dupterm_notify)

    # read magic word (16byte="UlnoIOT-NetREPL:"),
    # key (32byte=256bit) and iv (8byte=64bit)
    # but encrypted
    #init=decrypt_receive(last_client_socket,64,2000) # 2s timeout for init
    init=cc_in.receive(timeoutms=2000) # 2s timeout for init
    if init[0:16] == MAGIC: # Magic correct
        print("Initial handshake succeeded, received session key.")
        # use rest for output key
        cc_out =  chacha.ChaCha(init[16:48],init[48:64],socket=last_client_socket)

        # print in terminal: last_client_socket.sendall(bytes([255, 252, 34])) # dont allow line mode
        # print in terminal: last_client_socket.sendall(bytes([255, 251, 1])) # turn off local echo
    
        uos.dupterm(TelnetWrapper(cc_in,cc_out))
        # while True:
        #     d=cc_in.receive()
        #     if len(d)>0:
        #         d=bytes(d).decode().strip()
        #         print(d)
        #         if d.startswith("quit"):
        #             print("done")
        #             break
        #         v=None
        #         try:
        #             v=eval(d)
        #             print("result", v)
        #             cc_out.send(str(v))
        #         except Exception as e:
        #             print(e.args[0])
        #             cc_out.send(str(v))


    else:
        last_client_socket.sendall('Wrong protocol for ulnoiot netrepl.\n') # dont allow line mode
        last_client_socket.close()


def stop():
    global server_socket, last_client_socket
    uos.dupterm(None)
    if server_socket:
        server_socket.close()
    if last_client_socket:
        last_client_socket.close()


# start listening for telnet connections on port 23
def start(port=23,key=b'ulnoiot.netrepl.ulnoiot.netrepl.'): # TODO: take simpler default key as it will be reset
    stop()
    global server_socket, _key
    _key = key

    # will be initialized after connection
    # cc_out = chacha.ChaCha(key, bytes(8))
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    ai = socket.getaddrinfo("0.0.0.0", port)
    addr = ai[0][4]
    
    server_socket.bind(addr)
    server_socket.listen(1)
    server_socket.setsockopt(socket.SOL_SOCKET, 20, accept_telnet_connect)
    
    for i in (network.AP_IF, network.STA_IF):
        wlan = network.WLAN(i)
        if wlan.active():
            print("UlnoIOT netrepl server started on {}:{}".format(wlan.ifconfig()[0], port))
