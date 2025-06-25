"""
替换cookie为您的cookie（F12）
如果出现412错误请刷新cookie重试
经测试过可以实现所要求的各项功能
包括选择主题与选择uid
已上传至https://github.com/miletcxl/crawling_comment_of_Bilibili
-----------QWQ-----------
"""
import os
import re
import time
import random
import json
import sqlite3
import requests
import hashlib
import urllib.parse
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import jieba
from datetime import datetime
from wordcloud import WordCloud
from collections import defaultdict
from tqdm import tqdm
import platform
import warnings

warnings.filterwarnings("ignore")

#身份认证
COOKIE = "SESSDATA=b48d2ec1%2C1766397652%2C0117f%2A62CjBZQIcetaAQWAngx91p2LUDZw7iMOa4tQiH4lFjgP1AmUJf3ti-BBd8YYSBr2kQXc8SVjFCczRPV0R0U2U3ZkJTS19XeE1ENm9tUVN5eWpJUUhLRTQ3UUxsc1FzeTVhY0hGMEhIMlRGZ29QXzN5Q01CaDljSUNwMldDNUJmOUlWT2xhY1dOUnlBIIEC; buvid3=078B37F8-2329-7FEC-8B95-A425D0A1BC2757995infoc"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Cookie": COOKIE
}

DB_NAME = "bilibili_sentiment.db"
TABLE_POST = "posts"
TABLE_COMMENT = "comments"
TABLE_NEGATIVE = "negative_texts"

#关键词字典
NEGATIVE_KEYWORDS = {
    "涉政有害": ["反动", "颠覆", "分裂", "台独", "港独", "疆独", "藏独", "独裁", "暴政", "专制",
                "叛国", "渗透", "间谍", "政变", "暴动", "政权更替", "政治犯", "政治迫害", "颜色革命", "分裂国家",
                "反政府", "反体制", "反共", "反华", "反社会", "言论封锁", "政治清洗", "镇压", "暴力执法",
                "异见人士", "非法组织", "颠覆政权", "极端思想", "自由", "法轮功", "民运", "西方渗透",
                "敏感词", "境外势力", "煽动仇恨", "反贼", "抵制中央", "非法集资", "政权腐败", "人权问题",
                "强拆", "黑警", "维稳", "退党", "集体请愿", "境外网站", "网信办", "删帖", "封号""颠覆政体", "境外干预", "暗网政治", "非法言论", "境外反华", "敏感事件", "新闻封锁", "删帖控评", "封号潮", "政治黑幕",
                "替天行道", "革命火种", "翻墙", "网攻政府", "网络暴民", "暴政机器", "特权阶层", "执法黑幕", "政治献金", "非法游说"],

    "侮辱谩骂": ["傻逼", "狗东西", "废物", "死全家", "滚", "去死", "人渣", "畜生", "妈的", "白痴",
                "废柴", "贱人", "贱货", "婊子", "死妈", "舔狗", "脑瘫", "神经病", "垃圾", "弱智",
                "智障", "贱逼", "狗屎", "猪头", "王八蛋", "狗娘养的", "狗杂种", "狗日的", "龟儿子",
                "狗崽子", "饭桶", "草你妈", "你妈死了", "你全家死", "去你妈的", "死逼", "癞蛤蟆",
                "孬种", "丧家犬", "败类", "下贱", "下三滥", "臭不要脸", "白眼狼", "贱骨头", "懒蛤蟆",
                "无脑", "蠢货", "阴阳怪气", "穷鬼", "臭虫", "舔老", "臭傻子", "烂人", "二货", "臭不要脸",
                "睿智", "暴躁老哥", "狗头", "抬杠精","nt", "脑瘤", "狗东西", "低能儿", "烂货", "丧尽天良", "疯狗", "你个傻叉", "你配吗", "废话连篇",
                "满嘴喷粪", "杠精", "键盘侠", "脑袋进水", "你是来搞笑的吗", "你有病吧", "二百五", "撒比", "大傻子", "真他妈","cs"],

    "色情暴力": ["色情", "强奸", "性侵", "猥亵", "淫秽", "裸照", "露点", "性骚扰", "自慰", "做爱",
                "啪啪啪", "AV", "黄片", "胸大", "屁股", "色狼", "色鬼", "骚", "胸器", "性交易",
                "援交", "嫖娼", "卖淫", "淫乱", "女优", "乱伦", "肉体", "小黄片", "床戏", "漏点",
                "性奴", "调教", "射精", "成人片", "啪啪啪", "走光", "偷窥", "拍裸照", "SM", "乳沟",
                "处女", "小姐", "情趣", "内衣诱惑", "裸聊", "网黄", "直播造黄", "绳虐", "激情戏", "羞耻play",
                "暴力", "杀人", "砍人", "血腥", "虐杀","湿身", "大尺度", "肉欲", "性癖", "捆绑play", "开房", "约P", "啪啪视频", "巨乳", "车震",
                "乳摇", "漏毛", "舔胸", "舌吻", "69式", "菊花残", "情趣用品", "丝袜诱惑", "黑丝", "强暴"],

    "事故灾难":["爆炸", "火灾", "车祸", "空难", "沉船", "矿难", "地震", "台风", "洪水", "泥石流",
                "山体滑坡", "雪崩", "瘟疫", "疫情", "死亡", "伤亡", "重伤", "灾难", "核泄漏", "核污染",
                "灾害", "崩塌", "毒气", "泄露", "污染", "毒奶粉", "疫苗事故", "踩踏", "食物中毒", "病逝",
                "病故", "病倒", "病危", "医患冲突", "医闹", "地铁事故", "桥梁倒塌", "船翻", "航班失联", "恶劣天气",
                "山洪", "飓风", "水灾", "塌方", "爆破", "高温中暑", "溺水", "失踪", "毒酒", "中毒",
                "电梯事故", "化学泄漏","爆雷", "金融危机", "校园暴力", "塌楼", "煤气爆炸", "高空坠物", "失火", "食安事故", "疫苗异常", "公共安全事故",
                "群死群伤", "重大安全事故", "连环车祸", "重大伤亡", "突发事故", "重大隐患", "系统瘫痪", "重大故障", "交通瘫痪"],

    "聚集维权": ["游行", "示威", "罢工", "请愿", "集会", "维权", "抗议", "堵路", "堵门", "占领",
                "静坐", "围堵", "暴动", "冲突", "警民冲突", "清场", "抓捕", "非法集会", "非暴力不合作", "举报腐败",
                "上访", "堵桥", "围殴", "退房维权", "业主维权", "教师维权", "业主抗议", "校园抗议", "城管暴力", "逼迁",
                "社保断缴", "强拆", "断水断电", "政府失责", "群体事件", "农民维权", "企业维权", "讨薪", "集体罢工", "歇业抗议",
                "押金维权", "职工维权", "消费者维权", "业主群", "群体上访", "打横幅", "工地维权", "小区停工", "封门抗议", "罢市",
                "罢课", "交通阻断", "高楼抛物","网络维权", "集体维权", "业主聚集", "罢免", "声援", "组织集会", "举牌", "上街抗议", "横幅抗议", "举报无门",
                "维权事件", "堵小区", "围住政府", "校园请愿", "集体维权行动", "业主联盟", "工人维权", "网暴政府", "民间团体"],


    "娱乐八卦": ["出轨", "绯闻", "劈腿", "小三", "离婚", "分手", "私生饭", "吸毒", "嫖娼", "偷税",
                "漏税", "造假", "假唱", "抄袭", "剽窃", "包养", "潜规则", "丑闻", "不雅照", "整容",
                "整形", "双面人", "炒作", "耍大牌", "丑态", "黑历史", "私生活混乱", "负面新闻", "金主", "艳照",
                "艳门", "绯闻对象", "前任", "前女友", "撕逼", "骂战", "手撕", "不合", "约炮", "隐婚",
                "假恋情", "骗婚", "出柜", "骗粉", "蹭热度", "人设崩塌", "塌房", "粉丝撕逼", "八卦爆料", "狗仔",
                "床照", "网暴", "逼婚", "造人"]
}

def setup_chinese_font():
    """配置中文字体支持"""
    # 设置matplotlib默认字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    #可用的中文字体
    chinese_fonts = ['SimHei']
    available_fonts = []

    # 查找所有可用字体
    for font in fm.findSystemFonts():
        try:
            font_name = fm.FontProperties(fname=font).get_name()
            for cf in chinese_fonts:
                if cf.lower() in font_name.lower():
                    available_fonts.append(font)
                    break
        except:
            continue

    if available_fonts:
        # 使用找到的第一个中文字体
        font_path = available_fonts[0]
        font_prop = fm.FontProperties(fname=font_path)
        font_name = font_prop.get_name()

        # 设置全局字体
        plt.rcParams['font.family'] = font_name
        print(f"使用中文字体: {font_name}")
        return font_path
    else:
        # 如果找不到中文字体，使用默认字体
        print("警告: 未找到中文字体，图表中文可能显示为方框")
        return None


#全局设置中文字体
FONT_PATH = setup_chinese_font()

def load_stopwords(path="stopwords.txt"):
    """加载中文停用词表"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        print("警告：未找到 stopwords.txt，将使用默认空列表")
        return set()

def get_wbi_keys():
    try:
        res = requests.get("https://api.bilibili.com/x/web-interface/nav", headers=HEADERS, timeout=10)
        if res.status_code != 200:
            print(f"获取密钥失败: HTTP {res.status_code}")
            return None, None

        data = res.json()
        if data.get("code") != 0:
            print(f"获取密钥失败: {data.get('message')}")
            return None, None

        img_url = data['data']['wbi_img']['img_url']
        sub_url = data['data']['wbi_img']['sub_url']
        img_key = img_url.rsplit('/', 1)[1].split('.')[0] if img_url else ""
        sub_key = sub_url.rsplit('/', 1)[1].split('.')[0] if sub_url else ""
        return img_key, sub_key
    except Exception as e:
        print(f"获取密钥异常: {str(e)}")
        return None, None


def mixin_key(img_key, sub_key):
    """混合密钥生成签名"""
    if not img_key or not sub_key:
        return ""

    mixin_table = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52
    ]
    combined = img_key + sub_key
    return ''.join(combined[i] for i in mixin_table)[:32] if combined else ""


def build_signed_params(params):
    """构建带签名的请求参数"""
    img_key, sub_key = get_wbi_keys()
    if not img_key or not sub_key:
        print("无法获取签名密钥，使用原始参数")
        return params

    wbi_key = mixin_key(img_key, sub_key)
    if not wbi_key:
        return params

    params['wts'] = int(time.time())
    params = dict(sorted(params.items()))

    query = urllib.parse.urlencode(params)
    w_rid = hashlib.md5((query + wbi_key).encode('utf-8')).hexdigest()
    params['w_rid'] = w_rid
    return params

def get_aid(bvid):
    """获取视频 aid"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"获取 aid 失败: HTTP {res.status_code}")
            return None

        data = res.json()
        if data.get('code') != 0:
            print(f"获取 aid 失败: {data.get('message')}")
            return None

        return data['data']['aid']
    except Exception as e:
        print(f"获取 aid 异常: {str(e)}")
        return None

def search_videos_by_keyword(keyword, max_count=100):
    """关键词搜索视频"""
    url = "https://api.bilibili.com/x/web-interface/search/type"
    results = []
    page = 1

    while len(results) < max_count:
        params = {
            "search_type": "video",
            "keyword": keyword,
            "page": page,
            "page_size": min(20, max_count - len(results))
        }

        try:
            #添加 WBI 签名
            signed_params = build_signed_params(params)
            res = requests.get(url, headers=HEADERS, params=signed_params, timeout=15)

            if res.status_code != 200:
                print(f"搜索失败: HTTP {res.status_code}, 第 {page} 页")
                break

            data = res.json()
            if data.get('code') != 0:
                print(f"搜索失败: {data.get('message')}, 第 {page} 页")
                break

            videos = data['data'].get('result', [])
            if not videos:
                break

            for v in videos:
                #处理可能的空值
                title = re.sub(r'<.*?>', '', v.get('title', '无标题'))
                if not title.strip():
                    title = "无标题"

                desc = v.get('description', '无描述')
                if not desc.strip():
                    desc = "无描述"

                pubdate = v.get('pubdate', 0)
                try:
                    pubtime = datetime.fromtimestamp(pubdate).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pubtime = "未知时间"

                #构建评论区链接
                comment_url = f"https://www.bilibili.com/video/{v.get('bvid', '')}/#reply"

                results.append({
                    'bvid': v.get('bvid', ''),
                    'title': title,
                    'desc': desc,
                    'pubtime': pubtime,
                    'comment_url': comment_url
                })
                if len(results) >= max_count:
                    break

            page += 1
            time.sleep(random.uniform(1.5, 3.0))  # 增加随机延迟防封

        except Exception as e:
            print(f"搜索异常: {str(e)}")
            break

    return results

def get_user_videos(mid, max_count=50):
    """获取用户的所有视频"""
    url = "https://api.bilibili.com/x/space/wbi/arc/search"
    results = []
    page = 1
    page_size = 30  # 每页数量

    while len(results) < max_count:
        params = {
            "mid": mid,
            "ps": min(page_size, max_count - len(results)),
            "pn": page
        }

        try:
            # 添加 WBI 签名
            signed_params = build_signed_params(params)
            res = requests.get(url, headers=HEADERS, params=signed_params, timeout=15)

            if res.status_code != 200:
                print(f"获取用户视频失败: HTTP {res.status_code}, 第 {page} 页")
                break

            data = res.json()
            if data.get('code') != 0:
                print(f"获取用户视频失败: {data.get('message')}, 第 {page} 页")
                break

            vlist = data['data'].get('list', {}).get('vlist', [])
            if not vlist:
                break

            for v in vlist:
                # 构建评论区链接
                comment_url = f"https://www.bilibili.com/video/{v.get('bvid', '')}/#reply"

                results.append({
                    'bvid': v.get('bvid', ''),
                    'title': v.get('title', '无标题'),
                    'desc': v.get('description', '无描述'),
                    'pubtime': datetime.fromtimestamp(v.get('created', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                    'comment_url': comment_url
                })
                if len(results) >= max_count:
                    break

            page += 1
            time.sleep(random.uniform(1.0, 2.0))  # 增加随机延迟防封

        except Exception as e:
            print(f"获取用户视频异常: {str(e)}")
            break

    return results


def get_comments(aid, max_pages=3):
    """获取视频评论"""
    if not aid:
        return []

    all_comments = []
    next_page = 0
    page = 1

    while page <= max_pages:
        try:
            params = {
                "oid": aid,
                "type": 1,
                "mode": 3,
                "next": next_page,
                "ps": 30
            }

            #添加 WBI 签名
            signed_params = build_signed_params(params)
            url = "https://api.bilibili.com/x/v2/reply/main"
            res = requests.get(url, headers=HEADERS, params=signed_params, timeout=15)

            if res.status_code != 200:
                print(f"获取评论失败: HTTP {res.status_code}")
                break

            data = res.json()
            if data.get('code') != 0:
                print(f"获取评论失败: {data.get('message')}")
                break

            replies = data['data'].get('replies', [])
            if not replies:
                break

            for reply in replies:
                content = reply.get('content', {}).get('message', '')
                if content and content.strip():
                    all_comments.append(content.strip())

            #检查是否有下一页
            cursor = data['data'].get('cursor', {})
            if cursor.get('is_end', False):
                break

            next_page = cursor.get('next', 0)
            page += 1
            time.sleep(random.uniform(1.0, 2.5))  # 增加随机延迟防封

        except Exception as e:
            print(f"获取评论异常: {str(e)}")
            break

    return all_comments

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_POST} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bvid TEXT UNIQUE,
            title TEXT,
            desc TEXT,
            pubtime TEXT,
            comment_url TEXT
        )""")

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_COMMENT} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bvid TEXT,
            content TEXT
        )""")

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NEGATIVE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bvid TEXT,
            content TEXT,
            category TEXT,
            comment_url TEXT,
            match_score INTEGER
        )""")

    conn.commit()
    return conn


def insert_posts(conn, posts):
    for p in posts:
        conn.execute(
            f"INSERT OR IGNORE INTO {TABLE_POST} (bvid, title, desc, pubtime, comment_url) VALUES (?, ?, ?, ?, ?)",
            (p['bvid'], p['title'], p['desc'], p['pubtime'], p['comment_url']))
    conn.commit()

def insert_comments(conn, bvid, comments):
    for c in comments:
        conn.execute(f"INSERT INTO {TABLE_COMMENT} (bvid, content) VALUES (?, ?)", (bvid, c))
    conn.commit()


def detect_negatives(conn):
    """检测负面舆情并存入数据库"""
    cur = conn.cursor()
    #获取所有评论及其对应的评论区链接
    cur.execute(f"""
        SELECT c.bvid, c.content, p.comment_url 
        FROM {TABLE_COMMENT} c
        JOIN {TABLE_POST} p ON c.bvid = p.bvid
    """)
    rows = cur.fetchall()

    for bvid, content, comment_url in rows:
        for cat, words in NEGATIVE_KEYWORDS.items():
            match_score = sum(1 for w in words if w in content)
            if match_score >= 1:
                conn.execute(f"""
                    INSERT INTO {TABLE_NEGATIVE} 
                    (bvid, content, category, comment_url, match_score)
                    VALUES (?, ?, ?, ?, ?)""",
                             (bvid, content, cat, comment_url, match_score))
                break  #每条评论最多归入一个分类
    conn.commit()

def analyze_and_visualize(conn):
    """生成分析报告和图表"""
    # 确保报告目录存在
    os.makedirs("report", exist_ok=True)

    # 获取负面舆情数据
    try:
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NEGATIVE}", conn)
    except Exception as e:
        print(f"查询负面舆情数据失败: {str(e)}")
        df = pd.DataFrame()

    # 导出负面舆情到CSV
    if not df.empty:
        csv_path = "report/negative_comments.csv"
        df.to_csv(csv_path, index=False, encoding='utf_8_sig')
        print(f"负面舆情数据已导出到: {csv_path}")

    # 生成图表
    if df.empty:
        print("无负面舆情数据")
        # 生成空数据提示图
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, '无负面舆情数据',
                 ha='center', va='center', fontsize=20)
        plt.axis('off')
        plt.savefig("report/no_data.png")
        plt.close()
        return

    # 1. 类别分布柱状图
    plt.figure(figsize=(12, 8))

    # 确保有category列
    if 'category' not in df.columns:
        df['category'] = '未知'

    category_counts = df['category'].value_counts()

    # 创建自定义颜色
    colors = plt.cm.tab20c(range(len(category_counts)))

    # 绘制柱状图
    ax = category_counts.plot(
        kind='bar',
        color=colors,
        edgecolor='black'
    )

    # 设置标题和标签
    plt.title('负面舆情类别分布', fontsize=16, fontweight='bold')
    plt.xlabel('舆情类别', fontsize=12)
    plt.ylabel('出现次数', fontsize=12)

    # 旋转标签防止重叠
    if len(category_counts) > 5:
        plt.xticks(rotation=45, ha='right', fontsize=10)
    else:
        plt.xticks(fontsize=10)

    # 添加数值标签
    for i, v in enumerate(category_counts):
        ax.text(i, v + 0.5, str(v),
                ha='center',
                fontsize=9,
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig("report/category_distribution.png", dpi=150)
    plt.close()

    # 2. 词云图 - 使用停用词过滤后词频
    stopwords = load_stopwords()

    word_freq = defaultdict(int)
    for text in df['content']:
        words = jieba.cut(text)
        for word in words:
            if re.match(r'^[\u4e00-\u9fa5]{2,}$', word) and word not in stopwords:
                word_freq[word] += 1

    try:
        wordcloud = WordCloud(
            font_path=FONT_PATH,
            width=1200,
            height=800,
            background_color="white",
            max_words=200,
            colormap="Reds",
            contour_width=1,
            contour_color='steelblue'
        ).generate_from_frequencies(word_freq)

        plt.figure(figsize=(14, 10))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.title('负面舆情关键词云', fontsize=16, fontweight='bold')
        plt.axis("off")
        plt.savefig("report/wordcloud.png", dpi=150)
        plt.close()
    except Exception as e:
        print(f"生成词云图失败: {str(e)}")

    # 3. 时间趋势图
    try:
        #从帖子表中获取发布时间
        post_df = pd.read_sql_query(
            f"SELECT p.bvid, p.pubtime, n.category FROM {TABLE_POST} p "
            f"JOIN {TABLE_NEGATIVE} n ON p.bvid = n.bvid",
            conn
        )

        #确保有pubtime列
        if 'pubtime' in post_df.columns:
            # 转换时间格式
            post_df['pubdate'] = pd.to_datetime(post_df['pubtime'], errors='coerce').dt.date

            #过滤无效日期
            post_df = post_df.dropna(subset=['pubdate'])

            #按日期和类别分组
            trend_data = post_df.groupby(['pubdate', 'category']).size().unstack().fillna(0)

            #绘制趋势图
            if not trend_data.empty:
                plt.figure(figsize=(14, 8))
                for column in trend_data.columns:
                    plt.plot(trend_data.index, trend_data[column],
                             marker='o', label=column, linewidth=2)

                plt.title('负面舆情时间趋势', fontsize=16, fontweight='bold')
                plt.xlabel('日期', fontsize=12)
                plt.ylabel('负面舆情数量', fontsize=12)
                plt.legend(title='舆情类别')
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig("report/trend_analysis.png", dpi=150)
                plt.close()
    except Exception as e:
        print(f"生成趋势图时出错: {str(e)}")


def generate_analysis_report(conn):
    """生成文本分析报告"""
    report_path = "report/analysis_report.txt"

    #获取负面舆情数据
    try:
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NEGATIVE}", conn)
    except:
        df = pd.DataFrame()

    #获取统计数据
    total_comments = pd.read_sql_query(f"SELECT COUNT(*) FROM {TABLE_COMMENT}", conn).iloc[0, 0]
    total_negative = len(df)

    #创建报告
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("哔哩哔哩负面舆情分析报告\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总评论数: {total_comments}\n")
        f.write(f"负面舆情数: {total_negative}\n")
        f.write(f"负面舆情比例: {total_negative / total_comments * 100:.2f}%\n\n")

        if not df.empty:
            # 按类别统计
            category_counts = df['category'].value_counts()
            f.write("-" * 60 + "\n")
            f.write("负面舆情类别分布:\n")
            f.write("-" * 60 + "\n")
            for cat, count in category_counts.items():
                f.write(f"{cat}: {count} 条 ({count / total_negative * 100:.1f}%)\n")

            # 高频词统计
            f.write("\n" + "-" * 60 + "\n")
            f.write("负面舆情高频词 TOP 20:\n")
            f.write("-" * 60 + "\n")

            # 分词统计
            # 加载停用词
            stopwords = load_stopwords()

            # 只统计合法中文词 + 过滤停用词
            import re
            def is_valid_word(word):
                return re.match(r'^[\u4e00-\u9fa5]{2,}$', word)

            word_freq = defaultdict(int)
            for text in df['content']:
                words = jieba.cut(text)
                for word in words:
                    if is_valid_word(word) and word not in stopwords:
                        word_freq[word] += 1

            # 按频率排序
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

            for word, freq in sorted_words:
                f.write(f"{word}: {freq} 次\n")

            # 典型负面舆情示例
            f.write("\n" + "-" * 60 + "\n")
            f.write("典型负面舆情示例:\n")
            f.write("-" * 60 + "\n")

            sample_size = min(5, len(df))
            sample_df = df.sample(sample_size, random_state=42)

            for i, row in sample_df.iterrows():
                f.write(f"\n【{row['category']}】\n")
                f.write(f"内容: {row['content']}\n")
                f.write(f"评论区链接: {row['comment_url']}\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("分析完成\n")
        f.write("=" * 60 + "\n")

        f.write("\n" + "-" * 60 + "\n")
        f.write("最贴合主题的负面评论（关键词命中≥3）:\n")
        f.write("-" * 60 + "\n")

        # 按关键词命中数筛选
        strong_df = df[df['match_score'] >= 3].copy()

        if not strong_df.empty:
            sample_size = min(5, len(strong_df))
            top_matches = strong_df.sort_values(by="match_score", ascending=False).head(sample_size)

            for _, row in top_matches.iterrows():
                f.write(f"\n【{row['category']} - 命中{row['match_score']}词】\n")
                f.write(f"内容: {row['content']}\n")
                f.write(f"评论区链接: {row['comment_url']}\n")

    print(f"分析报告已生成: {report_path}")

def main():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("已删除旧数据库，准备重建…")

    conn = init_db()
    mode = input("选择模式：1) 关键词搜索 2) 用户ID爬取\n> ").strip()

    if mode == '1':
        keyword = input("请输入关键词：").strip()
        print(f"开始搜索关键词: {keyword}")

        # 设置爬取量
        max_count = 30
        posts = search_videos_by_keyword(keyword, max_count=max_count)

        if not posts:
            print("未找到相关视频")
            conn.close()
            return

        print(f"找到 {len(posts)} 个视频")
        insert_posts(conn, posts)

        # 添加进度条
        with tqdm(total=len(posts), desc="抓取评论") as pbar:
            for p in posts:
                aid = get_aid(p['bvid'])
                if aid:
                    comments = get_comments(aid, max_pages=2)
                    if comments:
                        insert_comments(conn, p['bvid'], comments)
                    time.sleep(random.uniform(3.0, 6.0))  # 增加视频间延迟
                else:
                    print(f"跳过视频 {p['bvid']} (获取aid失败)")
                pbar.update(1)

    elif mode == '2':
        mid = input("请输入用户ID：").strip()
        print(f"开始爬取用户ID: {mid} 的视频")

        # 设置爬取量
        max_count = 20
        videos = get_user_videos(mid, max_count)

        if not videos:
            print("未找到相关视频")
            conn.close()
            return

        print(f"找到 {len(videos)} 个视频")
        insert_posts(conn, videos)

        # 添加进度条
        with tqdm(total=len(videos), desc="抓取评论") as pbar:
            for v in videos:
                aid = get_aid(v['bvid'])
                if aid:
                    comments = get_comments(aid, max_pages=2)
                    if comments:
                        insert_comments(conn, v['bvid'], comments)
                    time.sleep(random.uniform(3.0, 6.0))  # 增加视频间延迟
                else:
                    print(f"跳过视频 {v['bvid']} (获取aid失败)")
                pbar.update(1)
    else:
        print("无效选择")
        conn.close()
        return

    print("开始负面舆情检测...")
    detect_negatives(conn)

    print("生成分析报告...")
    analyze_and_visualize(conn)
    generate_analysis_report(conn)

    conn.close()
    print("实验完成，报告请见 report/ 目录")

if __name__ == '__main__':
    main()