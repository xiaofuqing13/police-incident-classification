import pandas as pd
import re
import jieba

# 加载数据
data = pd.read_excel("merged_data.xlsx")  # 假设数据已经合并到一个文件

# 停用词和无关信息
t1 = ['民警', '辅警', '重复报警', '人称', '报警', '称', '有人', '同时', '几乎',
      '年', '月', '日', '时', '分', '带领', '(', ')', '（', '）', ',', '，', ' ', '*',
      '1', '2', '3', '4', '5', '6', '7', '8', '9', '0','重复','电话','联系电话','间','因']

# 加载停用词表
stopwords = set(t1 + ['的', '了', '在', '和', '是', '也', '而', '有', '被', '将', '可', '与', '对于'])

# 定义清洗函数
def clean_text(text):
    """
    清洗文本：
    1. 删除“重复报警”内容及其后的所有字符。
    2. 删除无关信息，例如日期、时间、停用词。
    3. 分词并去除停用词。
    """
    if not isinstance(text, str):
        return ""

    # 删除“重复报警”内容后的所有字符
    text = re.sub(r'重复报警.*$', '', text)

    # 去除无意义的字符，例如日期、时间和无关词
    text = ''.join([char for char in text if char not in t1])

    # 分词
    words = jieba.lcut(text)

    # 去除停用词
    words = [word for word in words if word not in stopwords and word.strip()]

    return ' '.join(words)

# 应用清洗函数到报警内容
print("正在清洗数据，请稍候...")
data['clean_content'] = data['报警内容'].apply(clean_text)

# 保存清洗后的数据
output_file = "cleaned_merged_data.xlsx"
data.to_excel(output_file, index=False)

print(f"数据清洗完成，结果已保存到 {output_file}")