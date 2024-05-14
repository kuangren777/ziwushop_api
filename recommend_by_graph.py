# -*- coding: utf-8 -*-
# @Time    : 2024/5/14 0:55
# @Author  : KuangRen777
# @File    : recommend_by_graph.py
# @Tags    :
from neo4j import GraphDatabase


class ProductRecommender:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def recommend_products_for_user(self, user_name):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {name: $user_name})-[:PREFERS]->(p:Product)<-[:HAS_TAG]-(t:Tag),
                  (other:Product)-[:HAS_TAG]->(t)
            WHERE NOT (u)-[:PREFERS]->(other)
            RETURN other.name AS product, collect(t.name) AS tags
            """, user_name=user_name)
            for record in result:
                print(f"推荐商品: {record['product']}，标签: {', '.join(record['tags'])}")


# 使用
recommender = ProductRecommender("neo4j://localhost:7687", "neo4j", "luomingyu")
recommender.recommend_products_for_user("张三")
recommender.close()
