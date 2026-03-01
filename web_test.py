import tkinter as tk
from tkinter import ttk, StringVar, messagebox
import fasttext
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import font_manager, rcParams
from wordcloud import WordCloud
from pyecharts.charts import Map
from pyecharts import options as opts
from snapshot_selenium import snapshot
from pyecharts.render import make_snapshot
from PIL import Image, ImageTk
from tkinterweb import HtmlFrame
# 加载 fastText 模型
MODEL_PATH = "fasttext_model.bin"  # 替换为你的模型路径
model = fasttext.load_model(MODEL_PATH)

# 设置全局字体
rcParams['font.family'] = font_manager.FontProperties(fname="/System/Library/Fonts/STHeiti Light.ttc").get_name()
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 加载合并后的数据表
data = pd.read_excel("cleaned_merged_data.xlsx")

# 分类标签与部门的对应关系
CATEGORY_GUIDANCE = {
    "求助": "建议您联系求助部门，我们已通知他们，请保持电话畅通！",
    "治安案件": "建议您联系治安部门处理，详细说明情况！",
    "纠纷": "建议您联系纠纷调解部门处理！",
    "举报": "建议您将详细举报内容提交到举报部门！",
    "刑事案件": "建议您立即报警并联系刑事案件处理部门！",
    "其他报警": "建议您咨询相关部门以获得帮助！"
}

# 地域映射：数值映射为中文省份
region_mapping = {
    1: '浙江省', 2: '江苏省', 3: '上海市', 4: '湖南省',
    5: '安徽省', 6: '广东省', 7: '湖北省', 8: '河南省', 9: '江西省',
}

def report_help():
    help_window = tk.Toplevel()
    help_window.title("我要报警求助")
    help_window.geometry("600x400")

    # 添加输入框
    input_label = tk.Label(help_window, text="请输入报警内容：", font=("Arial", 12))
    input_label.place(x=50, y=50)

    input_text = tk.Text(help_window, height=5, width=50)
    input_text.place(x=50, y=80)

    # 添加结果显示区域
    result_label = tk.Label(help_window, text="智能识别结果及建议：", font=("Arial", 12))
    result_label.place(x=50, y=180)

    suggestion_label = tk.Label(help_window, text="", font=("Arial", 12), wraplength=500, justify="left")
    suggestion_label.place(x=50, y=210)

    def process_report():
        content = input_text.get("1.0", "end").strip()
        if not content:
            messagebox.showerror("错误", "请输入报警内容！")
            return

        # 模型预测
        prediction = model.predict(content)
        category = prediction[0][0].replace("__label__", "")
        confidence = prediction[1][0]  # 获取置信度

        # 设置置信度阈值
        CONFIDENCE_THRESHOLD = 0.4
        if confidence < CONFIDENCE_THRESHOLD:
            guidance = "未能确定报警类别，建议您直接联系相关部门！"
        else:
            guidance = CATEGORY_GUIDANCE.get(category, "未识别报警类别，请联系相关部门！")

        # 显示结果
        suggestion_label.config(text=f"类别: {category} (置信度: {confidence:.2f})\n{guidance}")

    # 添加按钮
    report_button = tk.Button(help_window, text="提交报警内容", font=("Arial", 12), bg="lightblue", command=process_report)
    report_button.place(x=250, y=300)

# 搜索引擎功能
def search_engine():
    search_window = tk.Toplevel()
    search_window.title("百度搜索引擎")
    search_window.geometry("1000x700")

    frame = HtmlFrame(search_window)
    frame.pack(fill="both", expand=True)

    # 加载百度首页
    frame.load_website("http://www.baidu.com")

# 创建词云函数
def generate_wordcloud(text, title):
    window = tk.Toplevel()
    window.title(title)
    window.geometry("800x600")

    wordcloud = WordCloud(font_path="/System/Library/Fonts/STHeiti Light.ttc", width=800, height=600, background_color='white').generate(text)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    ax.set_title(title, fontsize=16)

    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack()

# 生成总词云
def show_total_wordcloud():
    all_text = " ".join(data['clean_content'].dropna())
    generate_wordcloud(all_text, "总词云")

# 生成类别词云
def show_category_wordcloud(category):
    category_text = " ".join(data[data['label'] == category]['clean_content'].dropna())
    generate_wordcloud(category_text, f"{category} 词云")

# 可视化性别分布
def show_gender_distribution():
    window = tk.Toplevel()
    window.title("性别分布")
    window.geometry("800x600")

    gender_data = data.groupby(['label', '报警人性别']).size().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(8, 6))
    labels = gender_data.index.tolist()
    female_counts = gender_data['女']
    male_counts = gender_data['男']

    bar_width = 0.35
    x = range(len(labels))

    ax.bar(x, female_counts, bar_width, label="女性", color="red")
    ax.bar([p + bar_width for p in x], male_counts, bar_width, label="男性", color="blue")

    ax.set_xticks([p + bar_width / 2 for p in x])
    ax.set_xticklabels(labels, rotation=45)
    ax.set_ylabel("人数")
    ax.set_title("性别分布")
    ax.legend()

    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack()

# 地域分布
def show_region_map():
    # 将发生地域列值转换为中文省份全称
    data['region_name'] = data['发生地域'].map(region_mapping)
    region_counts = data['region_name'].value_counts().reset_index()
    region_counts.columns = ['region', 'count']
    region_data = [(row['region'], row['count']) for _, row in region_counts.iterrows()]

    # 使用 Pyecharts 绘制地图
    def render_region_map():
        map_chart = (
            Map()
            .add("警情分布", region_data, "china")
            .set_global_opts(
                title_opts=opts.TitleOpts(title="警情地域分布"),
                visualmap_opts=opts.VisualMapOpts(max_=region_counts['count'].max(),
                                                  is_piecewise=True,
                                                  pieces=[
                                                      {"min": 10000, "label": '>10000', "color": "#801C1B"},
                                                      {"min": 1000, "max": 9999, "label": '1000-9999', "color": "#FF3030"},
                                                      {"min": 500, "max": 999, "label": '500-999', "color": "#FF4500"},
                                                      {"min": 100, "max": 499, "label": '100-499', "color": "#FF7F50"},
                                                      {"min": 10, "max": 99, "label": '10-99', "color": "#FFA500"},
                                                      {"min": 1, "max": 9, "label": '1-9', "color": "#FFDEAD"},
                                                      {"max": 0, "label": '0', "color": "white"}
                                                  ]
                                                  ),
            )

        )
        map_chart.render("region_map.html")  # 保存为 HTML
        make_snapshot(snapshot, map_chart.render(), "region_map.png")  # 保存为图片
        print("地域分布地图已生成")

    render_region_map()

    # 显示地图图片
    window = tk.Toplevel()
    window.title("地域分布地图")
    window.geometry("900x600")
    img = Image.open("region_map.png")
    map_img = ImageTk.PhotoImage(img)
    label = tk.Label(window, image=map_img)
    label.image = map_img
    label.pack()

# 事件性质分布
def show_event_distribution():
    window = tk.Toplevel()
    window.title("事件性质分布")
    window.geometry("800x600")

    event_data = data['label'].value_counts()

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(event_data.values, labels=event_data.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("事件性质分布")

    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack()

# 主窗口
main_window = tk.Tk()
main_window.title("警情数据查询系统")
main_window.geometry("800x600")

# 菜单栏
menu_bar = tk.Menu(main_window)
main_window.config(menu=menu_bar)

# 搜索引擎菜单
menu_bar.add_command(label="搜索引擎", command=search_engine)

# 案件分布菜单
case_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="案件分布", menu=case_menu)
case_menu.add_command(label="性别分布", command=show_gender_distribution)
case_menu.add_command(label="地域分布地图", command=show_region_map)
case_menu.add_command(label="事件性质分布", command=show_event_distribution)

# 词云菜单
wordcloud_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="词云分析", menu=wordcloud_menu)
wordcloud_menu.add_command(label="总词云", command=show_total_wordcloud)
wordcloud_menu.add_command(label="求助词云", command=lambda: show_category_wordcloud("求助"))
wordcloud_menu.add_command(label="治安案件词云", command=lambda: show_category_wordcloud("治安案件"))
wordcloud_menu.add_command(label="纠纷词云", command=lambda: show_category_wordcloud("纠纷"))
wordcloud_menu.add_command(label="举报词云", command=lambda: show_category_wordcloud("举报"))
wordcloud_menu.add_command(label="其他报警词云", command=lambda: show_category_wordcloud("其它报警"))
wordcloud_menu.add_command(label="刑事案件词云", command=lambda: show_category_wordcloud("刑事案件"))

# 添加“我要报警求助”菜单
report_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="我要报警求助", menu=report_menu)
report_menu.add_command(label="报警求助", command=report_help)

# 主界面内容
label = tk.Label(main_window, text="警情数据查询系统", font=("Arial", 24))
label.pack(pady=20)
search_engine()
main_window.mainloop()