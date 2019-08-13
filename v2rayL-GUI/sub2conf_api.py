# -*- coding:utf-8 -*-
# Author: Suummmmer
# Date: 2019-08-13

import base64
import json
import pickle
import requests
from config import conf_template as conf


class Sub2Conf(object):
    def __init__(self, subs_url=None, conf_url=None):
        # 订阅原始数据
        self.origin = []

        self.subs_url = subs_url
        self.conf_url = conf_url

        # 解析后配置
        try:
            with open("/etc/v2rayL/data", "rb") as f:
                self.saved_conf = pickle.load(f)
        except:
            self.saved_conf = {
                "local": {},
                "subs": {}
            }

        self.conf = dict(self.saved_conf['local'], **self.saved_conf['subs'])

        '''
        self.conf结构
        {
            "地区"： "配置"
        }

        配置为解析得到的内容 + 协议
        '''

    def b642conf(self, prot, tp, b64str):
        if prot == "vmess":
            ret = eval(base64.b64decode(b64str).decode())
            region = ret['ps']

        elif prot == "ss":
            string = b64str.split("#")
            cf = string[0].split("@")
            if len(cf) == 1:
                tmp = base64.b64decode(cf[0]).decode()
            else:
                tmp = base64.b64decode(cf[0]).decode() + "@" + cf[1]
            ret = {
                "method": tmp.split(":")[0],
                "port": tmp.split(":")[2],
                "password": tmp.split(":")[1].split("@")[0],
                "add": tmp.split(":")[1].split("@")[1],
            }
            region = string[1]

        ret["prot"] = prot
        self.saved_conf[["local", "subs"][tp]][region] = ret

    def setconf(self, region):
        use_conf = self.conf[region]
        if use_conf['prot'] == "vmess":
            conf['outbounds'][0]["protocol"] = "vmess"
            conf['outbounds'][0]["settings"]["vnext"] = list()
            conf['outbounds'][0]["settings"]["vnext"].append({
                "address": use_conf["add"],
                "port": int(use_conf["port"]),
                "users": [
                    {
                        "id": use_conf["id"],
                        "alterId": use_conf["aid"]
                    }
                ]
            })

            conf['outbounds'][0]["streamSettings"] = {
                "network": use_conf["net"],
                "wsSettings": {
                    "path": use_conf["path"],
                    "headers": {
                        "Host": use_conf['host']
                    }
                }
            }

        elif use_conf['prot'] == "ss":
            conf['outbounds'][0]["protocol"] = "shadowsocks"
            conf['outbounds'][0]["settings"]["servers"] = list()
            conf['outbounds'][0]["settings"]["servers"].append({
                "address": use_conf["add"],
                "port": int(use_conf["port"]),
                "password": use_conf["password"],
                "ota": False,
                "method": use_conf["method"]
            })
            conf['outbounds'][0]["streamSettings"] = {
                "network": "tcp"
            }

        with open("/etc/v2rayL/config.json", "w") as f:
            f.write(json.dumps(conf, indent=4))

    def delconf(self, region):
        self.conf.pop(region)
        try:
            self.saved_conf['local'].pop(region)
        except KeyError:
            self.saved_conf['subs'].pop(region)
        except:
            raise MyException("配置删除出错，请稍后再试..")

        with open("/etc/v2rayL/data", "wb") as jf:
            pickle.dump(self.saved_conf, jf)

    def update(self):
        """
        更新订阅
        """
        try:
            ret = requests.get(self.subs_url)
            if ret.status_code != 200:
                raise MyException("无法获取订阅信息，订阅站点访问失败")
            all_subs = base64.b64decode(ret.text + "==").decode().strip()
            if "vmess" not in all_subs or "ss" not in all_subs:
                raise MyException("解析订阅信息失败，请确认链接正确")
            all_subs = all_subs.split("\n")
        except:
            raise MyException("解析订阅信息失败")

        for sub in all_subs:
            self.origin.append(sub.split("://"))

        self.saved_conf["subs"] = {}

        for ori in self.origin:
            if ori[0] == "vmess":
                self.b642conf("vmess", 1, ori[1])
            elif ori[0] == "ss":
                self.b642conf("ss", 1, ori[1])

        self.conf = dict(self.saved_conf['local'], **self.saved_conf['subs'])

        with open("/etc/v2rayL/data", "wb") as jf:
            pickle.dump(self.saved_conf, jf)

    def add_conf_by_uri(self):
        """
        通过分享的连接添加配置
        """
        try:
            op = self.conf_url.split("://")
            if op[0] == "vmess":
                self.b642conf("vmess", 0, op[1])
            elif op[0] == "ss":
                self.b642conf("ss", 0, op[1])
            else:
                raise MyException("无法解析的链接格式")
        except Exception:
            raise MyException("解析失败，请在github提交错误")

        self.conf = dict(self.saved_conf['local'], **self.saved_conf['subs'])

        with open("/etc/v2rayL/data", "wb") as jf:
            pickle.dump(self.saved_conf, jf)

    def conf2b64(self, region):
        tmp = dict()
        prot = self.conf[region]['prot']
        for k, v in self.conf[region].items():
            tmp[k] = v
        tmp.pop("prot")
        if prot == "vmess":
            return prot+"://"+base64.b64encode(str(tmp).encode()).decode()
        else:
            return prot+"://"+base64.b64encode("{}:{}@{}:{}".format(tmp["method"],
                                                                       tmp["password"], tmp["add"],
                                                                       tmp["port"]).encode()).decode()+"#"+region


# 异常
class MyException(Exception):
    def __init__(self, *args):
        self.args = args


# if __name__ == '__main__':
#     # s = Sub2Conf("https://sub.qianglie.xyz/subscribe.php?sid=4594&token=TCDWnwMD0rGg")
#     # print(s.conf)
#
#     # s.setconf("1.0x TW-BGP-A 台湾")
#
#     # t = base64.b64decode("ewoidiI6ICIyIiwKInBzIjogIjIzM3YyLmNvbV8xNDIuOTMuNTAuNzgiLAoiYWRkIjogIjE0Mi45My41MC43OCIsCiJwb3J0IjogIjM5Mzk4IiwKImlkIjogIjc1Y2JmYzI0LTZhNjAtNDBmMC05Yjc2LTUyMTlmNTIwYTJlMCIsCiJhaWQiOiAiMjMzIiwKIm5ldCI6ICJrY3AiLAoidHlwZSI6ICJ1dHAiLAoiaG9zdCI6ICIiLAoicGF0aCI6ICIiLAoidGxzIjogIiIKfQo=").decode().strip()
#     # print(t)
#
#     b642conf("ss", "YWVzLTI1Ni1jZmI6NTQxNjAzNDY2QDE0Mi45My41MC43ODo5ODk4#ss")