# -*- coding: utf-8 -*-
# @Time    : 2024/5/10 11:56
# @Author  : KuangRen777
# @File    : recommend_user_profile.py
# @Tags    : 基于用户画像推荐
import pandas as pd
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics.pairwise import cosine_similarity


# 自定义jieba分词的tokenizer函数
def jieba_tokenizer(text):
    return jieba.lcut(text)


# 扩展商品数据
products = pd.DataFrame({
    'product_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    'name': [
        '草本茶', '维生素C', '蛋白棒', '有机蜂蜜', '芦荟胶', '护肤霜', '燕麦片', '绿茶', '按摩油', '蜂胶',
        '薄荷糖', '薰衣草精油', '姜茶', '抗氧化果汁', '矿泉水', '综合坚果', '保湿面膜', '天然维E', '消化酵素', '低糖饼干'
    ],
    'description': [
        '清新舒缓的草本茶，适合女性',
        '高浓度维生素C补充剂，适合男性',
        '含坚果和巧克力的能量蛋白棒，适合男性',
        '不含添加剂的纯有机蜂蜜，适合女性',
        '保湿镇定的芦荟胶，适合南方潮湿气候',
        '营养丰富的护肤霜，适合北方干燥天气',
        '健康早餐燕麦片，适合东部忙碌生活',
        '提神醒脑的绿茶，适合西部山区',
        '放松身心的按摩油，适合中老年人',
        '增强免疫力的蜂胶，适合所有年龄',
        '清凉提神的薄荷糖，适合办公室人士',
        '帮助睡眠的薰衣草精油，适合压力大的人',
        '暖胃去寒的姜茶，适合冷天气',
        '抗老化的抗氧化果汁，适合追求健康的人',
        '纯净水源的矿泉水，适合所有人',
        '多种营养的综合坚果，适合需要能量的人',
        '补水抗皱的保湿面膜，适合关注肌肤的人',
        '天然抗氧化的维E，适合老年人',
        '帮助消化的酵素，适合饮食不规律的人',
        '低糖健康的饼干，适合糖尿病患者'
    ],
    'price': [10, 15, 8, 12, 20, 25, 5, 7, 30, 22, 9, 28, 13, 19, 2, 18, 21, 16, 17, 6],
    'brand': [
        '品牌A', '品牌B', '品牌C', '品牌D', '品牌E', '品牌F', '品牌G', '品牌H', '品牌I', '品牌J',
        '品牌K', '品牌L', '品牌M', '品牌N', '品牌O', '品牌P', '品牌Q', '品牌R', '品牌S', '品牌T'
    ],
    'rating': [4.5, 4.2, 4.8, 4.7, 4.3, 4.6, 4.1, 4.0, 4.9, 4.4, 4.3, 4.8, 4.2, 4.7, 4.1, 4.5, 4.6, 4.3, 4.4, 4.2],
    'preferred_gender': ['female', 'male', 'male', 'female', 'female', 'female', 'male', 'male', 'female', 'all', 'all',
                         'female', 'all', 'all', 'all', 'all', 'female', 'all', 'all', 'all'],
    'preferred_region': ['南方', '北方', '东部', '西部', '南方', '北方', '东部', '西部', '中部', '全国', '全国', '全国',
                         '北方', '南方', '东部', '西部', '全国', '中部', '全国', '全国']
})

# 扩展用户数据
users = pd.DataFrame({
    'user_id': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120],
    'age': [25, 30, 22, 40, 35, 45, 55, 60, 33, 27, 29, 31, 38, 42, 50, 53, 28, 34, 48, 37],
    'gender': ['male', 'female', 'female', 'male', 'female', 'male', 'female', 'male', 'female', 'male', 'female',
               'male', 'female', 'male', 'female', 'male', 'female', 'male', 'female', 'male'],
    'region': ['北方', '南方', '东部', '西部', '北方', '南方', '东部', '西部', '南方', '北方', '东部', '西部', '南方',
               '北方', '东部', '西部', '南方', '北方', '东部', '西部']
})

# 用户购买记录
user_purchases = pd.DataFrame({
    'user_id': [101, 102, 101, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
    'product_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
})

# 用户购买记录
user_purchases = pd.DataFrame({
    'user_id': [101, 102, 101],
    'product_id': [1, 2, 3]
})

# 文本特征提取
text_features = 'description'
text_transformer = Pipeline(steps=[
    ('tfidf', TfidfVectorizer(tokenizer=jieba_tokenizer))
])

# 数值特征提取
numeric_features = ['price', 'rating']
numeric_transformer = StandardScaler()

# 类别特征提取
categorical_features = ['brand', 'preferred_gender', 'preferred_region']
categorical_transformer = OneHotEncoder()

# 构建预处理管道
preprocessor = ColumnTransformer(
    transformers=[
        ('text', text_transformer, text_features),
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ]
)

# 应用预处理步骤
X_transformed = preprocessor.fit_transform(products)

# 计算相似度
cosine_sim = cosine_similarity(X_transformed, X_transformed)


# 结合用户行为和属性推荐
def personalized_recommend(user_id, user_purchases, cosine_sim, products, users, top_n=20):
    # 基于用户特征进行筛选，例如年龄、地区等
    user_info = users[users['user_id'] == user_id].iloc[0]
    potential_products = products.copy()

    # 根据性别和地区进行过滤
    gender_pref_products = potential_products[potential_products['preferred_gender'] == user_info['gender']]
    region_pref_products = potential_products[potential_products['preferred_region'] == user_info['region']]

    # 合并性别和地区偏好的产品，同时考虑年龄价格过滤
    potential_products = pd.concat([gender_pref_products, region_pref_products]).drop_duplicates()
    if user_info['age'] > 30:
        potential_products = potential_products[potential_products['price'] > 10]

    # 重置索引，以确保索引是连续的
    potential_products = potential_products.reset_index(drop=True)

    # 基于用户购买历史的推荐
    purchased_indices = user_purchases[user_purchases['user_id'] == user_id]['product_id'].tolist()
    product_indices = potential_products.index.tolist()
    # 获取用户购买商品的索引在原始商品列表中的位置
    purchased_indices_positions = [products.index.get_loc(pid) for pid in purchased_indices if
                                   pid in products['product_id'].values]
    # 计算与购买历史相似的商品分数
    sim_scores = cosine_sim[purchased_indices_positions][:, product_indices].mean(axis=0)
    sim_scores = [(i, score) for i, score in enumerate(sim_scores)]
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[:top_n]
    recommended_indices = [i for i, _ in sim_scores]

    return potential_products.iloc[recommended_indices]


# 调整显示设置，以便完整打印 DataFrame
pd.set_option('display.max_columns', None)  # 显示所有列
pd.set_option('display.max_rows', None)  # 显示所有行
pd.set_option('display.max_colwidth', None)  # 显示完整的列宽，使所有内容都可见
pd.set_option('display.width', None)  # 自动调整显示宽度

# 测试推荐系统
user_id = 101
recommended_products = personalized_recommend(user_id, user_purchases, cosine_sim, products, users)
print(recommended_products)
