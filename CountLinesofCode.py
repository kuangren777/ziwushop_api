# -*- coding: utf-8 -*-
# @Time    : 2024/4/28 1:58
# @Author  : KuangRen777
# @File    : CountLinesofCode.py
# @Tags    :
import os


def count_lines_of_code(directory):
    total_lines = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_lines += len(lines)
    return total_lines


if __name__ == "__main__":
    directory = input("请输入项目目录路径：")
    lines_of_code = count_lines_of_code(directory)
    print(f"项目代码行数：{lines_of_code}")
