import pandas as pd
import fasttext
import jieba
import os

# 加载数据
x_train = pd.read_excel('X_train.xlsx')
y_train = pd.read_excel('y_train.xlsx')
x_test = pd.read_excel('X_test.xlsx')
y_test = pd.read_excel('y_test.xlsx')

# 合并训练集和测试集
x_data = pd.concat([x_train, x_test], axis=0, ignore_index=True)
y_data = pd.concat([y_train, y_test], axis=0, ignore_index=True)

# 加载停用词表
stopwords = set(pd.read_csv("/Users/xiaofuqing/PycharmProjects/大作业/基于文本分类方法的警情数据处理和自助报警的实现/警情数据集/cn_stopwords.txt", header=None, names=["stopword"])["stopword"])

# 文本清洗函数
def clean_text(text):
    """清洗文本：去除无用字符和停用词"""
    text = ''.join([char for char in text if char.isalnum() or char.isspace()])
    words = jieba.lcut(text)
    words = [word for word in words if word not in stopwords]
    return ' '.join(words)

# 对数据集的文本内容进行清洗
x_data['clean_content'] = x_data['报警内容'].apply(clean_text)

# 合并标签数据
data = pd.concat([x_data['clean_content'], y_data], axis=1)
data.columns = ['content', 'label']

# 格式化为 fastText 格式
def format_fasttext(row):
    return f"__label__{row['label']} {row['content']}"

data['fasttext_format'] = data.apply(format_fasttext, axis=1)

# 划分训练集和测试集
train_data = data.sample(frac=0.8, random_state=42)  # 80% 训练集
test_data = data.drop(train_data.index)              # 20% 测试集

# 保存为 fastText 格式文件
os.makedirs("./data", exist_ok=True)
train_data['fasttext_format'].to_csv("./data/train_data.txt", index=False, header=False)
test_data['fasttext_format'].to_csv("./data/test_data.txt", index=False, header=False)

# 模型训练
model = fasttext.train_supervised(
    input="./data/train_data.txt",
    label="__label__",
    wordNgrams=2,  # 使用 n-gram
    epoch=25,      # 训练轮数
    lr=0.6,        # 学习率
    dim=100        # 词向量维度
)

# 测试模型
test_result = model.test("./data/test_data.txt")
print(f"测试集准确率: {test_result[1]:.2f}, 精度: {test_result[2]:.2f}")

# 保存模型
model.save_model("fasttext_model.bin")
print("模型已保存为 fasttext_model.bin")