# -*- coding: utf-8 -*-
# @Time    : 2024/5/10 15:20
# @Author  : KuangRen777
# @File    : recommend_good_to_good.py
# @Tags    : 商品间推荐TF-IDF
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import word_tokenize
import nltk
import jieba

nltk.download('punkt')

def jieba_tokenizer(text):
    return jieba.lcut(text)

# 假设的商品数据
products = pd.DataFrame({
    'product_id': range(1, 21),
    'name': [
        '草本茶', '维生素C', '蛋白棒', '有机蜂蜜', '芦荟胶',
        '护肤霜', '燕麦片', '绿茶', '按摩油', '蜂胶',
        '薄荷糖', '薰衣草精油', '姜茶', '抗氧化果汁', '矿泉水',
        '综合坚果', '保湿面膜', '天然维E', '消化酵素', '低糖饼干'
    ],
    'description': [
        '清新舒缓的草本茶，适合女性', '高浓度维生素C补充剂，适合男性',
        '含坚果和巧克力的能量蛋白棒', '不含添加剂的纯有机蜂蜜', '保湿镇定的芦荟胶，适合南方潮湿气候',
        '营养丰富的护肤霜，适合北方干燥天气', '健康早餐燕麦片，适合东部忙碌生活', '提神醒脑的绿茶，适合西部山区',
        '放松身心的按摩油，适合中老年人', '增强免疫力的蜂胶，适合所有年龄',
        '清凉提神的薄荷糖，适合办公室人士', '帮助睡眠的薰衣草精油，适合压力大的人',
        '暖胃去寒的姜茶，适合冷天气', '抗老化的抗氧化果汁，适合追求健康的人', '纯净水源的矿泉水，适合所有人',
        '多种营养的综合坚果，适合需要能量的人', '补水抗皱的保湿面膜，适合关注肌肤的人', '天然抗氧化的维E，适合老年人',
        '帮助消化的酵素，适合饮食不规律的人', '低糖健康的饼干，适合糖尿病患者'
    ]
})

# 假设的用户评价数据
user_reviews = pd.DataFrame({
    'product_id': list(range(1, 21)) * 2,  # 模拟更多的用户评价
    'review': [
                  '这是一款我非常喜欢的草本茶，味道很不错', '维生素C真的很适合我，感觉身体棒棒的',
                  '蛋白棒味道好极了，特别是巧克力味', '有机蜂蜜很纯正，甜而不腻', '芦荟胶很适合夏天使用，清凉舒缓',
                  '这款护肤霜很滋润，冬天用很合适', '燕麦片是我每天早餐的选择', '绿茶味道清新，提神醒脑',
                  '按摩油很好用，缓解了我的肩颈疼痛', '蜂胶提高了我的免疫力',
                  '薄荷糖很提神，上班必备', '薰衣草精油帮我缓解了睡眠问题', '姜茶暖胃，很适合冬天饮用',
                  '抗氧化果汁让我感觉更健康', '矿泉水很纯净，口感很好',
                  '综合坚果营养丰富，很适合户外运动时补充能量', '保湿面膜让我的皮肤更加滋润',
                  '天然维E很适合中老年人补充',
                  '消化酵素帮我解决了消化不良的问题', '低糖饼干对控制血糖很有帮助'
              ] * 2
})

# 合并商品描述和用户评价
combined_texts = products[['product_id', 'description']].copy()
combined_texts = combined_texts.merge(user_reviews, on='product_id')
combined_texts['combined_text'] = combined_texts['description'] + ' ' + combined_texts['review']

# 提取文本特征
vectorizer = TfidfVectorizer(tokenizer=word_tokenize, stop_words='english')
text_features = vectorizer.fit_transform(combined_texts['combined_text'])

# 计算商品间的余弦相似度
product_similarity = cosine_similarity(text_features, text_features)

# 为简化起见，我们取每个商品第一个相似度计算结果作为示例
product_similarity_df = pd.DataFrame(product_similarity, index=combined_texts['product_id'],
                                     columns=combined_texts['product_id'])


# 定义推荐函数
def recommend_based_on_text(item_id, product_similarity_df, products, top_n=5):
    # 确保商品ID在数据集中
    if item_id not in product_similarity_df.index:
        return "商品ID不存在，请检查商品ID。"

    # 获取与指定商品最相似的商品
    similar_items = product_similarity_df[item_id].mean(axis=0).sort_values(ascending=False)

    # 选择得分最高的 top_n 个商品
    top_similar_items = similar_items.head(top_n + 1).index.tolist()
    top_similar_items.remove(item_id)  # 移除自身

    # 返回推荐商品的信息
    return products[products['product_id'].isin(top_similar_items)]


# 测试推荐
item_id = 2
recommended_products = recommend_based_on_text(item_id, product_similarity_df, products)
print("基于商品 {} 推荐的其他商品:".format(item_id))
print(recommended_products[['product_id', 'name']])
