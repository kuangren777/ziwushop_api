# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 16:50
# @Author  : KuangRen777
# @File    : utils.py
# @Tags    :
from datetime import datetime


def transfer_time(input_time_str):
    # 将输入时间字符串解析为 datetime 对象
    input_time = datetime.fromisoformat(input_time_str)

    # 将 datetime 对象格式化为所需格式的时间字符串
    output_time_str = input_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return output_time_str


def build_tree(elements, parent_id=0):
    branch = []
    for element in elements:
        if element.pid == parent_id:
            children = build_tree(elements, element.id)
            node = {
                'id': element.id,
                'pid': element.pid,
                'name': element.name,
                'level': element.level,
                'status': element.status,
                'seq': 1
            }
            if children:  # 只有当有子分类时才添加 `children` 字段
                node['children'] = children
            branch.append(node)
    return branch

