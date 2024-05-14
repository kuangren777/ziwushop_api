import pymysql
from neo4j import GraphDatabase
from datetime import datetime

# 从 MySQL 数据库获取数据
def fetch_data_from_mysql():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='luomingyu',
        database='ziwushop_api',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM Users")
            users = cursor.fetchall()
            cursor.execute("SELECT * FROM Goods")
            goods = cursor.fetchall()
            cursor.execute("SELECT * FROM Category")
            categories = cursor.fetchall()
            cursor.execute("SELECT * FROM Comments")
            comments = cursor.fetchall()
            cursor.execute("SELECT * FROM Orders")
            orders = cursor.fetchall()
            cursor.execute("SELECT * FROM OrderDetails")
            order_details = cursor.fetchall()
            cursor.execute("SELECT * FROM Address")
            addresses = cursor.fetchall()
    finally:
        connection.close()

    return users, goods, categories, comments, orders, order_details, addresses


# 生成 Cypher 命令

def generate_cypher(users, goods, categories, comments, orders, order_details, addresses):
    cypher_commands = []

    for user in users:
        cypher_commands.append(
            f"CREATE (:User {{id: {user['id']}, name: '{user['name']}', email: '{user['email']}'}})"
        )

    for good in goods:
        cypher_commands.append(
            f"CREATE (:Product {{id: {good['id']}, title: '{good['title']}', price: {good['price']}, category_id: {good['category_id']}}})"
        )

    for category in categories:
        cypher_commands.append(
            f"CREATE (:Category {{id: {category['id']}, name: '{category['name']}'}})"
        )

    for comment in comments:
        cypher_commands.append(
            f"CREATE (:Comment {{id: {comment['id']}, content: '{comment['content']}', rate: {comment['rate']}, star: {comment['star']}}})"
        )

    for order in orders:
        # Check if 'created_at' is a string or a datetime object and format accordingly
        if isinstance(order['created_at'], str):
            created_at = datetime.strptime(order['created_at'], "%Y-%m-%d %H:%M:%S.%f").isoformat()
        elif isinstance(order['created_at'], datetime):
            created_at = order['created_at'].isoformat()
        else:
            raise TypeError("Unexpected type for created_at; expected str or datetime.datetime")

        cypher_commands.append(
            f"CREATE (:Order {{id: {order['id']}, order_no: '{order['order_no']}', amount: {order['amount']}, created_at: datetime('{created_at}')}})"
        )

    for detail in order_details:
        cypher_commands.append(
            f"CREATE (:OrderDetail {{id: {detail['id']}, price: {detail['price']}, num: {detail['num']}}})"
        )

    for address in addresses:
        cypher_commands.append(
            f"CREATE (:Address {{id: {address['id']}, city: '{address['city']}', province: '{address['province']}'}})"
        )

    # Creating relationships
    for good in goods:
        cypher_commands.append(
            f"MATCH (p:Product {{id: {good['id']}}}), (c:Category {{id: {good['category_id']}}}) CREATE (p)-[:TAGGED_AS]->(c)"
        )

    for comment in comments:
        cypher_commands.append(
            f"MATCH (u:User {{id: {comment['user_id']}}}), (c:Comment {{id: {comment['id']}}}), (p:Product {{id: {comment['goods_id']}}}) CREATE (u)-[:WROTE]->(c), (p)-[:HAS_COMMENT]->(c)"
        )

    for order in orders:
        cypher_commands.append(
            f"MATCH (u:User {{id: {order['user_id']}}}), (o:Order {{id: {order['id']}}}), (a:Address {{id: {order['address_id']}}}) CREATE (u)-[:PLACED]->(o), (o)-[:DELIVERED_TO]->(a)"
        )

    for detail in order_details:
        cypher_commands.append(
            f"MATCH (o:Order {{id: {detail['order_id']}}}), (d:OrderDetail {{id: {detail['id']}}}), (p:Product {{id: {detail['goods_id']}}}) CREATE (o)-[:INCLUDES]->(d), (d)-[:OF_PRODUCT]->(p)"
        )

    for address in addresses:
        cypher_commands.append(
            f"MATCH (u:User {{id: {address['user_id']}}}), (a:Address {{id: {address['id']}}}) CREATE (u)-[:LIVES_AT]->(a)"
        )

    # 建立用户间基于共同兴趣的商品的潜在联系
    for user1 in users:
        for user2 in users:
            if user1['id'] != user2['id'] and user1['id'] % 3 == user2['id'] % 3:
                cypher_commands.append(
                    f"MATCH (u1:User {{id: {user1['id']}}}), (u2:User {{id: {user2['id']}}}) CREATE (u1)-[:SIMILAR_INTEREST]->(u2)"
                )

    # 建立用户与其愿望清单中商品的关系
    for user in users:
        for good in goods:
            if user['id'] % 4 == good['id'] % 4:  # 示例启发式规则，表示可能的偏好
                cypher_commands.append(
                    f"MATCH (u:User {{id: {user['id']}}}), (p:Product {{id: {good['id']}}}) CREATE (u)-[:WISHED]->(p)"
                )

    # 建立商品间基于经常一起购买的关系
    for order in orders:
        products = [detail['goods_id'] for detail in order_details if detail['order_id'] == order['id']]
        for i in range(len(products)):
            for j in range(i + 1, len(products)):
                cypher_commands.append(
                    f"MATCH (p1:Product {{id: {products[i]}}}), (p2:Product {{id: {products[j]}}}) CREATE (p1)-[:OFTEN_BOUGHT_WITH]->(p2)"
                )

    # 根据用户评价为商品建立信誉关系
    for comment in comments:
        if comment['star'] >= 4:
            cypher_commands.append(
                f"MATCH (p:Product {{id: {comment['goods_id']}}}), (u:User {{id: {comment['user_id']}}}) CREATE (p)-[:HIGHLY_RATED_BY]->(u)"
            )

    # 根据订单地址分析商品在不同地区的热销情况
    for order in orders:
        address_id = order['address_id']
        products = [detail['goods_id'] for detail in order_details if detail['order_id'] == order['id']]
        for product_id in products:
            cypher_commands.append(
                f"MATCH (p:Product {{id: {product_id}}}), (a:Address {{id: {address_id}}}) CREATE (p)-[:HOT_IN]->(a)"
            )

    return cypher_commands


# 导入数据到 Neo4j
def import_data_to_neo4j(cypher_commands):
    uri = "neo4j://localhost:7687"
    user = "neo4j"
    password = "luomingyu"

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        for command in cypher_commands:
            session.run(command)
    driver.close()


# 推荐系统类
class ProductRecommender:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

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
            print("Based on Purchase Time:")
            for record in result:
                print(f"Product: {record['p']['title']}, Relevance: {record['relevance']}")

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
            print("Based on User Location:")
            for record in result:
                print(f"Product: {record['p']['title']}, Relevance: {record['relevance']}")

    def recommend_based_on_season(self, user_id):
        current_season = "冬季"
        with self.driver.session() as session:
            result = session.run("""
            MATCH (p:Product)-[:TAGGED_AS]->(c:Category {name: $season})
            RETURN p, COUNT(*) AS relevance
            ORDER BY relevance DESC
            LIMIT 10
            """, season=current_season)
            print("Based on Seasonal Trends:")
            for record in result:
                print(f"Product: {record['p']['title']}, Relevance: {record['relevance']}")


# 使用示例
if __name__ == "__main__":
    users, goods, categories, comments, orders, order_details, addresses = fetch_data_from_mysql()
    cypher_commands = generate_cypher(users, goods, categories, comments, orders, order_details, addresses)
    import_data_to_neo4j(cypher_commands)

    # 创建推荐器实例
    recommender = ProductRecommender("neo4j://localhost:7687", "neo4j", "luomingyu")

    # 测试用户 ID
    test_user_id = 1

    # 执行推荐
    recommender.recommend_based_on_purchase_time(test_user_id)
    recommender.recommend_based_on_user_location(test_user_id)
    recommender.recommend_based_on_season(test_user_id)

    # 关闭数据库连接
    recommender.close()
