#!/usr/bin/env python

# @package      HAProxy Galera Monitoring Agent
# @author       Matt Hanley

import multiprocessing
import json
import requests
import os
import time
import copy
import hashlib
import sys
import threading
import uuid

import socket
import MySQLdb

# Globals
previous = None
proc_end = False
debug = True
checkFlowcontrol = False

healthyGalera ={
    'wsrep_cluster_status': 'Primary',
    'wsrep_connected': 'ON',
    #'wsrep_flow_control_paused': '<1',
    #'wsrep_flow_control_recv': 12,
    #'wsrep_flow_control_sent': 0,
    #'wsrep_local_recv_queue': 0,
    'wsrep_local_state_comment': 'Synced',
    'wsrep_ready': 'ON',
    'read_only': 'OFF',
}

def log(message, always=False):
    if always or debug:
        thread = 'Main' if isinstance(threading.current_thread(), threading._MainThread) else str(threading.current_thread().ident)
        print '[' + thread + '] ' + message

def getStatus(result):
    available = '200 OK'
    unavailable = '503 Service Unavailable'
    for key, value in healthyGalera.items():
        if (key not in result or result[key] != value):
            return unavailable
    if checkFlowcontrol and result['wsrep_flow_control_paused'] > 0.8:
        return unavailable
    return available

def checkDatabase():
    result = {}
    db = MySQLdb.connect(
        host="localhost",
        user="haproxy",
        passwd="")
    cur = db.cursor()
    for query in [
        "SHOW VARIABLES LIKE 'read_only'",
        "SHOW STATUS LIKE '%wsrep%'",
    ]:
        cur.execute(query)
        for row in cur.fetchall():
            result[row[0]] = row[1]
    if checkFlowcontrol:
        # Optional; requires `GRANT RELOAD ON *.* to 'haproxy'@'%';`
        cur.execute("FLUSH LOCAL STATUS")
    db.close()
    return result

def socketListen(s):
    conn, addr = s.accept()
    dbStatus = checkDatabase()
    message = {}
    message['status'] = dbStatus
    message = json.dumps(message)
    conn.send(
        "HTTP/1.1 "
        + getStatus(dbStatus)
        + "\nContent-Type: application/json\nContent-Length: "
        + str(len(message))
        + "\n\n"
        + message
        + "\n")
    conn.close()

def main():
    log('Monitoring agent starting...', True)

    TCP_IP = '0.0.0.0'
    TCP_PORT = 3305

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(2)
    while not proc_end:
        _timer_start = time.time()
        threadSocketListen = threading.Thread(target=socketListen, args=(s,))
        #threadSocketListen.daemon = True
        threadSocketListen.start()
        log('Started thread ' + str(threadSocketListen.ident), True)
        threadSocketListen.join()
        _runtime = time.time() - _timer_start
        log('Run time: ' + str(_runtime))
    s.close()
if __name__ == "__main__":
    main()
