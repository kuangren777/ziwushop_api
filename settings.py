# -*- coding: utf-8 -*-
# @Time    : 2024/4/25 23:57
# @Author  : KuangRen777
# @File    : settings.py
# @Tags    :
# create database ziwushop_api default charset utf8;
TORTOISE_ORM = {
    'connections': {
        'default': {
            # 'engine': 'tortoise.backends.asyncpg',  PostgreSQL
            'engine': 'tortoise.backends.mysql',  # MySQL or Mariadb
            'credentials': {
                'host': '127.0.0.1',
                'port': '3306',
                'user': 'root',
                'password': 'luomingyu',
                'database': 'ziwushop_api',
                'minsize': 1,
                'maxsize': 5,
                "echo": True
            }
        },
    },
    'apps': {
        'models': {
            'models': ['models', "aerich.models"],
            'default_connection': 'default',

        }
    },
    'use_tz': False,
    'timezone': 'Asia/Shanghai'
}
