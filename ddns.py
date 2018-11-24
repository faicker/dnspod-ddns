#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import signal
import functools
import logging
import socket
import time
from urllib import request, error, parse
from config import read_config, save_config, check_config, cfg
from get_ip import get_ip

def header():
    h = {
        'User-Agent': 'Client/0.0.1 ({})'.format(cfg['email'])
    }
    return h

def get_record_id(domain, sub_domain):
    url = 'https://dnsapi.cn/Record.List'
    params = parse.urlencode({
        'login_token': cfg['login_token'],
        'format': 'json',
        'domain': domain
    })
    req = request.Request(url=url, data=params.encode('utf-8'), method='POST', headers=header())
    try:
        resp = request.urlopen(req).read().decode()
    except (error.HTTPError, error.URLError, socket.timeout):
        return None
    records = json.loads(resp).get('records', {})
    for item in records:
        if item.get('name') == sub_domain:
            return item.get('id')
    return None


def update_record(ip):
    url = 'https://dnsapi.cn/Record.Modify'
    params = parse.urlencode({
        'login_token': cfg['login_token'],
        'format': 'json',
        'domain': cfg['domain'],
        'sub_domain': cfg['sub_domain'],
        'record_id': cfg['record_id'],
        'record_line': '默认',
        'record_type': 'A',
        'ttl': 60,
        'value': ip,
    })
    req = request.Request(url=url, data=params.encode('utf-8'), method='POST', headers=header())
    resp = request.urlopen(req).read().decode()
    records = json.loads(resp)
    cfg['last_update_time'] = str(time.gmtime())
    logging.info("record updated: %s" % records)


def main():
    running = True
    def handler(signum, frame):
        logging.info("killed")
        nonlocal running
        running = False
    signal.signal(signal.SIGTERM, handler)
    try:
        interval = int(cfg['interval'])
    except ValueError:
        interval = 5
    while running:
        current_ip = get_ip(cfg['using_local_ip'])
        if current_ip:
            # 对于拥有多个出口 IP 负载均衡的服务器，上面的 get_ip() 函数会在几个 ip 之间不停切换
            # 然后频繁进入这个判断，进行 update_record()，然后很快就会触发 API Limited 了
            # 于是建立一个IP池记载这个服务器的几个出口IP，以免频繁切换
            
            ip_count = int(cfg['ip_count'])
            ip_pool = cfg['ip_pool'].split(',')[:ip_count]
            cfg['current_ip'] = current_ip
            if current_ip not in ip_pool:
                # new ip found
                logging.info("new ip found: %s", current_ip)
                
                ip_pool.insert(0, current_ip)
                cfg['ip_pool'] = ','.join([str(x) for x in ip_pool[:ip_count]])
                update_record(current_ip)
                save_config()
        else:
            logging.error('get current ip FAILED.')
        time.sleep(interval)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s : %(message)s')
    logging.info('start...')
    read_config()
    check_config()
    cfg['record_id'] = get_record_id(cfg['domain'], cfg['sub_domain'])
    if cfg['record_id'] is None:
        logging.error("get record_id failed")
        sys.exit(1)
    logging.info("get record_id: %s" % str(cfg['record_id']))
    logging.info("watching ip for ddns: %s.%s" % (cfg['sub_domain'], cfg['domain']))

    try:
        main()
    except KeyboardInterrupt:
        logging.info("CTRL+C")
    finally:
        logging.info("stopped")
