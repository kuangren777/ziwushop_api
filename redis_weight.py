# -*- coding: utf-8 -*-
# @Time    : 2024/5/14 15:26
# @Author  : KuangRen777
# @File    : redis_weight.py
# @Tags    :
import redis


class RedisWeightsManager:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)

    def set_weights(self, user_id, weights):
        weights_key = f"user:{user_id}:weights"
        for key, value in weights.items():
            self.redis.hset(weights_key, key, value)
        print(f"Current User {user_id} Weights:", self.get_weights(user_id))

    def get_weights(self, user_id):
        weights_key = f"user:{user_id}:weights"
        retrieved_weights = self.redis.hgetall(weights_key)
        return {key.decode('utf-8'): float(value) for key, value in retrieved_weights.items()}

    def set_global_weights(self, weights):
        global_weights_key = "user:global:weights"
        for key, value in weights.items():
            self.redis.hset(global_weights_key, key, value)
        print(f"Current Global Weights:", self.get_global_weights())

    def get_global_weights(self):
        global_weights_key = "user:global:weights"
        retrieved_weights = self.redis.hgetall(global_weights_key)
        return {key.decode('utf-8'): float(value) for key, value in retrieved_weights.items()}

    def get_user_weights_else_global(self, user_id):
        user_weights = self.get_weights(user_id)
        if user_weights:
            return user_weights
        else:
            gb_weights = self.get_global_weights()
            self.set_weights(user_id, gb_weights)
            return gb_weights


# 示例使用
if __name__ == "__main__":
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

    manager = RedisWeightsManager()

    # 设置全局权重
    manager.set_global_weights(weights)

    # 获取全局权重
    global_weights = manager.get_global_weights()
    print("Global Weights:", global_weights)

    # 设置特定用户权重
    user_id = '5'
    # manager.set_weights(user_id, weights)

    # 获取特定用户权重
    user_weights = manager.get_weights(user_id)
    print(f"User {user_id} Weights:", user_weights)
