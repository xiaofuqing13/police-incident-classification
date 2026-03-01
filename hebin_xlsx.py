import pandas as pd

# 假设这些表是通过读取文件获得的
x_train = pd.read_excel("X_train.xlsx")
y_train = pd.read_excel("y_train.xlsx")
x_test = pd.read_excel("X_test.xlsx")
y_test = pd.read_excel("y_test.xlsx")

# 为训练集和测试集分别添加标签
x_train['label'] = y_train

x_test['label'] = y_test

# 合并训练集和测试集
merged_data = pd.concat([x_train, x_test], ignore_index=True)

# 保存合并后的表为新文件
merged_data.to_excel("merged_data.xlsx", index=False)

# 打印新表的基本信息
print("合并后的表：")
print(merged_data.head())
print(f"表的总记录数：{len(merged_data)}")