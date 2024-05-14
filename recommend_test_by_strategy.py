# -*- coding: utf-8 -*-
# @Time    : 2024/5/14 1:22
# @Author  : KuangRen777
# @File    : recommend_test_by_strategy.py
# @Tags    :
from neo4j import GraphDatabase
from PASSWORD import *


def recommend_for_user(user_id, weights=None):
    if weights is None:
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

    recommendations = {}
    recommender = ProductRecommender()

    rec_functions = [
        ("history", recommender.recommend_based_on_history),
        ("price_sensitivity", recommender.recommend_based_on_price_sensitivity),
        ("similar_categories", recommender.recommend_based_on_similar_categories),
        ("purchase_time", recommender.recommend_based_on_purchase_time),
        ("similar_interest", recommender.recommend_based_on_similar_interest),
        ("wishlist", recommender.recommend_based_on_wishlist),
        ("often_bought_together", recommender.recommend_based_on_often_bought_together),
        ("high_ratings", recommender.recommend_based_on_high_ratings),
        ("regional_trends", recommender.recommend_based_on_regional_trends)
    ]

    for name, func in rec_functions:
        recs = func(user_id)
        for goods_id, relevance in recs:
            if goods_id not in recommendations:
                recommendations[goods_id] = 0
            recommendations[goods_id] += relevance * weights.get(name, 1.0)

    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    return sorted_recommendations[:10]  # Returning top 10 recommendations


def adjust_weights_for_product(user_id, product_id, current_weights, increase_type="view"):
    if increase_type == "view":
        increase_factor = 1.1
    elif increase_type == "purchase":
        increase_factor = 1.5
    elif increase_type == "add_cart":
        increase_factor = 1.3
    else:
        increase_factor = 1.0
        print('Invalid increase type')
    # Adjust weights for algorithms that recommend the specified product
    recommender = ProductRecommender()
    weight_adjustments = {
        "history": recommender.recommend_based_on_history,
        "price_sensitivity": recommender.recommend_based_on_price_sensitivity,
        "similar_categories": recommender.recommend_based_on_similar_categories,
        "purchase_time": recommender.recommend_based_on_purchase_time,
        "similar_interest": recommender.recommend_based_on_similar_interest,
        "wishlist": recommender.recommend_based_on_wishlist,
        "often_bought_together": recommender.recommend_based_on_often_bought_together,
        "high_ratings": recommender.recommend_based_on_high_ratings,
        "regional_trends": recommender.recommend_based_on_regional_trends
    }

    for name, func in weight_adjustments.items():
        recs = func(user_id=user_id)
        if any(product_id == rec[0] for rec in recs):
            current_weights[name] *= increase_factor

    # print(current_weights)

    return current_weights


class ProductRecommender:
    def __init__(self, uri=NEO4J_BASE_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def recommend_based_on_history(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $userId})-[:PLACED]->(o:Order)-[:INCLUDES]->(od:OrderDetail)-[:OF_PRODUCT]->(p:Product)
            MATCH (p)-[:TAGGED_AS]->(c:Category)
            MATCH (rec:Product)-[:TAGGED_AS]->(c)
            WHERE NOT (u)-[:PLACED]->(:Order)-[:INCLUDES]->(:OrderDetail)-[:OF_PRODUCT]->(rec)
            RETURN rec, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on Purchase and Browsing History:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['rec']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['rec']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_comments(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $userId})-[:WROTE]->(com:Comment)-[:HAS_COMMENT]->(p:Product)-[:TAGGED_AS]->(c:Category)
            MATCH (rec:Product)-[:TAGGED_AS]->(c)
            WHERE NOT (u)-[:WROTE]->(:Comment)-[:HAS_COMMENT]->(rec)
            RETURN rec, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on Comments:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['rec']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['rec']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_price_sensitivity(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $userId})-[:PLACED]->(o:Order)-[:INCLUDES]->(od:OrderDetail)-[:OF_PRODUCT]->(p:Product)
            WITH u, AVG(p.price) AS avgPrice
            MATCH (rec:Product)
            WHERE abs(rec.price - avgPrice) < 100
            RETURN rec, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on Price Sensitivity:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['rec']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['rec']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_similar_categories(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $userId})-[:PLACED]->(o:Order)-[:INCLUDES]->(od:OrderDetail)-[:OF_PRODUCT]->(p:Product)-[:TAGGED_AS]->(c:Category)
            MATCH (rec:Product)-[:TAGGED_AS]->(c)
            WHERE NOT (u)-[:PLACED]->(:Order)-[:INCLUDES]->(:OrderDetail)-[:OF_PRODUCT]->(rec)
            RETURN rec, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on Categories Similarity:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['rec']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['rec']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_purchase_time(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $userId})-[:PLACED]->(o:Order)
            WHERE date(o.created_at).month = date(datetime()).month
            MATCH (o)-[:INCLUDES]->(od:OrderDetail)-[:OF_PRODUCT]->(p:Product)
            RETURN p, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on Purchase Time:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['p']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['p']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_user_location(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $userId})-[:LIVES_AT]->(a:Address)
            MATCH (p:Product)-[:TAGGED_AS]->(c:Category)
            WHERE a.city = '指定的城市名'
            RETURN p, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on User Location:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['p']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['p']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_season(self, user_id):
        current_season = "冬季"
        with self.driver.session() as session:
            result = session.run("""
            MATCH (p:Product)-[:TAGGED_AS]->(c:Category {name: $season})
            RETURN p, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, season=current_season)
            # print("Based on Seasonal Trends:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['p']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['p']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_similar_interest(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $userId})-[:SIMILAR_INTEREST]->(other:User)
            MATCH (other)-[:PLACED|:WISHED]->(:Order)-[:INCLUDES]->(:OrderDetail)-[:OF_PRODUCT]->(p:Product)
            RETURN p, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on Similar User Interests:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['p']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['p']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_wishlist(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $userId})-[:WISHED]->(wishedProduct:Product)
            MATCH (wishedProduct)-[:TAGGED_AS]->(c:Category)<-[:TAGGED_AS]-(similarProduct:Product)
            WHERE NOT (u)-[:PLACED|:WISHED]->(similarProduct)
            RETURN similarProduct, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on Wishlist:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['similarProduct']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['similarProduct']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_often_bought_together(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $userId})-[:PLACED]->(:Order)-[:INCLUDES]->(:OrderDetail)-[:OF_PRODUCT]->(p:Product)
            MATCH (p)-[:OFTEN_BOUGHT_WITH]->(frequentlyBought:Product)
            RETURN frequentlyBought, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on Frequently Bought Together:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['frequentlyBought']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['frequentlyBought']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_high_ratings(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (p:Product)-[:HIGHLY_RATED_BY]->(:User)
            RETURN p, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on High Ratings:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['p']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['p']['id'], record['relevance']))
            return recommend_list

    def recommend_based_on_regional_trends(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $userId})-[:LIVES_AT]->(a:Address)
            MATCH (p:Product)-[:HOT_IN]->(a)
            RETURN p, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, userId=user_id)
            # print("Based on Regional Trends:")
            recommend_list = []
            for record in result:
                # print(f"Product: {record['p']['title']}, Relevance: {record['relevance']}")
                recommend_list.append((record['p']['id'], record['relevance']))
            return recommend_list


# 使用示例
if __name__ == "__main__":
    # 实例化推荐器
    recommender = ProductRecommender()

    for i in range(1, 2):
        # 测试用户ID，请替换为您的测试用户ID
        test_user_id = i

        print(i)
        for recommend_goods, relevance in recommend_for_user(i):
            print(f"Recommendation for user {test_user_id}: {recommend_goods} (Relevance: {relevance})")

        # 执行推荐
        # recommender.recommend_based_on_history(test_user_id)
        # recommender.recommend_based_on_comments(test_user_id)  # 几乎不行
        # recommender.recommend_based_on_price_sensitivity(test_user_id)
        # recommender.recommend_based_on_similar_categories(test_user_id)
        # recommender.recommend_based_on_purchase_time(test_user_id)  # 可以一些
        # recommender.recommend_based_on_user_location(test_user_id) # 几乎不行
        # recommender.recommend_based_on_season(test_user_id)  # 几乎不行
        # recommender.recommend_based_on_similar_interest(test_user_id)
        # recommender.recommend_based_on_wishlist(test_user_id)
        # recommender.recommend_based_on_often_bought_together(test_user_id)
        # recommender.recommend_based_on_high_ratings(test_user_id)
        # recommender.recommend_based_on_regional_trends(test_user_id)

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

    adjust_weights_for_product(4, 2, weights, )

    # 关闭数据库连接
    recommender.close()
