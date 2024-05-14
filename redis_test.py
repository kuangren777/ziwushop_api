# -*- coding: utf-8 -*-
# @Time    : 2024/5/14 15:13
# @Author  : KuangRen777
# @File    : redis_test.py
# @Tags    :
import redis

# 连接到Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# 设置用户权重
# user_id = '1'
global_weights_key = f"user:global:weights"
# weights_key = f"user:{user_id}:weights"
weights = {
    "history": 1.0,
    "price_sensitivity": 1.0,
    "similar_categories": 1.0,
    "purchase_time": 1.0,
    "similar_interest": 1.0,
    "wishlist": 1.0,
    "often_bought_together": 1.0,
    "high_ratings": 1.0,
    "regional_trends": 1.0
}

# 使用 hset 命令存储字典中的键值对
for key, value in weights.items():
    r.hset(global_weights_key, key, value)

# 从Redis中获取存储的数据
retrieved_weights = r.hgetall(global_weights_key)

# 将字节类型的键和值转换为原始的字典结构
converted_weights = {key.decode('utf-8'): float(value) for key, value in retrieved_weights.items()}

# 打印转换后的字典
print(converted_weights)