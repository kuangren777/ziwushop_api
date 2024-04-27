# -*- coding: utf-8 -*-
# @Time    : 2024/4/28 1:11
# @Author  : KuangRen777
# @File    : delivery_query.py
# @Tags    :
import hashlib
import json

import requests
from PASSWORD import *


class KuaiDi100:
    def __init__(self):
        self.key = DELIVERY_KEY
        self.customer = DELIVERY_CUSTOMER
        self.url = 'https://poll.kuaidi100.com/poll/query.do'  # 请求地址

    def real_track(self, com, num, phone, ship_from, ship_to):
        """
        物流轨迹实时查询
        :param com: 查询的快递公司的编码，一律用小写字母
        :param num: 查询的快递单号，单号的最大长度是32个字符
        :param phone: 收件人或寄件人的手机号或固话（也可以填写后四位，如果是固话，请不要上传分机号）
        :param ship_from: 出发地城市，省-市-区，非必填，填了有助于提升签收状态的判断的准确率，请尽量提供
        :param ship_to: 目的地城市，省-市-区，非必填，填了有助于提升签收状态的判断的准确率，且到达目的地后会加大监控频率，请尽量提供
        :return: requests.Response.text
        """
        param = {
            'com': com,
            'num': num,
            'phone': phone,
            'from': ship_from,
            'to': ship_to,
            'resultv2': '1',  # 添加此字段表示开通行政区域解析功能。0：关闭（默认），1：开通行政区域解析功能，2：开通行政解析功能并且返回出发、目的及当前城市信息
            'show': '0',  # 返回数据格式。0：json（默认），1：xml，2：html，3：text
            'order': 'desc'  # 返回结果排序方式。desc：降序（默认），asc：升序
        }
        param_str = json.dumps(param)  # 转json字符串

        # 签名加密， 用于验证身份， 按param + key + customer 的顺序进行MD5加密（注意加密后字符串要转大写）， 不需要“+”号
        temp_sign = param_str + self.key + self.customer
        md = hashlib.md5()
        md.update(temp_sign.encode())
        sign = md.hexdigest().upper()
        request_data = {'customer': self.customer, 'param': param_str, 'sign': sign}
        return requests.post(self.url, request_data).text  # 发送请求

    def track(self, com, num, phone, ship_from, ship_to):
        """
        模拟物流轨迹实时查询
        :param com: 查询的快递公司的编码，一律用小写字母
        :param num: 查询的快递单号，单号的最大长度是32个字符
        :param phone: 收件人或寄件人的手机号或固话（也可以填写后四位，如果是固话，请不要上传分机号）
        :param ship_from: 出发地城市，省-市-区，非必填，填了有助于提升签收状态的判断的准确率，请尽量提供
        """
        if num == "156156131846523189":
            a = """{"message":"ok","nu":"156156131846523189","ischeck":"0","com":"shentong","status":"200","data":[{"time":"2024-04-27 05:17:36","context":"[深圳市]快件已发往【上海浦东转运中心】","ftime":"2024-04-27 05:17:36","areaCode":"CN440300000000","areaName":"广东,深圳市","status":"在途"},{"time":"2024-04-27 05:14:26","context":"[深圳市]快件已到达【广东深圳转运中心】","ftime":"2024-04-27 05:14:26","areaCode":"CN440300000000","areaName":"广东,深圳市","status":"在途"},{"time":"2024-04-27 03:15:10","context":"[东莞市]快件已发往【广东深圳转运中心】","ftime":"2024-04-27 03:15:10","areaCode":"CN441900000000","areaName":"广东,东莞市","status":"在途"},{"time":"2024-04-27 02:57:33","context":"[东莞市]快件已发往【广东深圳转运中心】","ftime":"2024-04-27 02:57:33","areaCode":"CN441900000000","areaName":"广东,东莞市","status":"在途"},{"time":"2024-04-27 02:52:19","context":"[东莞市]快件已到达【广东东莞虎门集散中心】","ftime":"2024-04-27 02:52:19","areaCode":"CN441900000000","areaName":"广东,东莞市","status":"在途"},{"time":"2024-04-26 21:35:28","context":"[东莞市]【广东东莞大郎营业部】(076983078692)的陈超(13267537570)已揽收","ftime":"2024-04-26 21:35:28","areaCode":"CN441900003000","areaName":"广东,东莞市,东城街道","status":"揽收"}],"state":"0","condition":"00"}"""
        else:
            a = """{"result":false,"returnCode":"500","message":"查询无结果，请隔段时间再查"}"""
        return a


if __name__ == '__main__':
    result = KuaiDi100().track('shentong', '156156131846523189', '', '', '')
    print(result)
    if 'result' in json.loads(result):
        print('暂无物流信息')
    else:
        print(json.loads(result)['data'][0]['context'])
