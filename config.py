#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import getopt
import sys
import logging

# 定义配置文件目录
# linux
config_path = '/etc/dnspod/ddnsrc'
# windows
if os.name == 'nt':
    config_path = 'ddnspod.cfg'

# 配置属性，及其默认参数
cfg = {}

# dnspod 登录配置
cfg["login_token"] = ''             # 默认空参数，要求用户必填 格式 'token_id,token'  # 登录token

# ddns 基本配置
cfg["sub_domain"] = ''              # 默认空参数，要求用户必填 #格式 'www'  # 子域名
cfg["domain"] = ''                  # 默认空参数，要求用户必填 #格式 'domain.com'  # 域名
cfg["interval"] = '5'               # 最小更新间隔
cfg["record_id"] = '{auto}'         # 记录id，程序自动生成
cfg["current_ip"] = '{auto}'        # 当前ip，程序自动生成
cfg["using_local_ip"] = '0'         # 是否使用本地ip
cfg["email"] = ''                   # 默认空参数，要求用户必填 #格式 'you@email.com'

# ip 池
cfg["ip_count"] = '1'               # 此域名拥有的ip数量，默认为 1 ， OpenWrt 玩家可能会有多个IP
cfg["ip_pool"] = '{auto}'           # ip 池 ..，程序自动生成
cfg["last_update_time"] = '{auto}'  # 上次更新成功时间戳，程序自动生成


def read_config():
    # 配置文件可指定
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hf:")
        for opt, arg in opts:
            if opt == '-f':
                if not os.path.exists(arg):
                    print("config file %s not exist" % arg)
                    print_help()
                    sys.exit(1)
                global config_path
                config_path = arg
            elif opt == '-h':
                print_help()
                sys.exit(1)
    except getopt.GetoptError:
        pass
    # 后面读出的数据会覆盖前面的
    read_config_from_file()
    read_config_from_env()
    read_config_from_argv()


def print_help():
    max_key_len = max([len(key) for key in cfg.keys()])
    print("ddns.py [-h|-f|...]")
    print("命令行方式调用，可用的参数如下：")
    fmt = '    --%-' + str(max_key_len) + 's <value>'
    for name in cfg.keys():
        print(fmt % name)
    print("配置优先级: 命令行 > 环境变量 > 配置文件")
    print("当前配置文件目录为：%s" % config_path)


def read_config_from_file():
    try:
        with open(config_path, 'r') as fp:
            for line in fp:
                pair = [x.strip() for x in line.split('=')]
                if pair[0] and pair[1]:
                    cfg[pair[0].lower()] = pair[1]
    except:
        pass


def read_config_from_env():
    for key in cfg:
        if os.getenv(key) is not None:
            cfg[key] = os.getenv(key)

# 从命令行读取参数


def read_config_from_argv():
    available_args = [x + "=" for x in cfg.keys()]
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hf:", available_args)
        for opt, arg in opts:
            if opt.startswith('--'):
                pair = [opt[2:], arg]
                if pair[0] and pair[1]:
                    cfg[pair[0].lower()] = pair[1]
    except getopt.GetoptError:
        print_help()
        sys.exit(1)


def save_config():
    try:
        save_config_to_file()
    except NotImplementedError as err:
        logging.error("FAILED to save config:" + str(err))

# 保存配置到文件… 这个函数现在会把配置文件里的注释也删掉……


def save_config_to_file():
    max_key_len = max([len(key) for key in cfg.keys()])
    try:
        with open(config_path, "w+") as f:
            f.writelines([
                ('%-'+str(max_key_len)+'s=%s\n') % (key, cfg[key])
                for key in cfg.keys()
            ])
    except IOError as err:
        logging.error("FAILED to save config to file: " + str(err))

# 检查配置是否齐全
def check_config():
    if not (
            cfg['login_token'] and
            cfg['domain'] and
            cfg['sub_domain']):
        logging.fatal('config error: need login info')
        sys.exit(1)
    try:
        if not(int(cfg["interval"])):
            logging.fatal('interval error')
            sys.exit(1)
        if not(int(cfg["ip_count"])):
            logging.fatal('ip_count error')            
            sys.exit(1)
    except:
        logging.fatal('config error')
        sys.exit(1)
    logging.info('config checked')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-8s: %(message)s')
    # 测试配置文件
    logging.info("init cfg: %s" % cfg)
    read_config()
    logging.info("read cfg: %s" % cfg)
    check_config()
