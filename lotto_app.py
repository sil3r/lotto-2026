import streamlit as st
import pandas as pd
import random
import requests
from bs4 import BeautifulSoup

# 設定網頁標題
st.set_page_config(page_title="2026 大樂透分析神器 (真實資料版)", page_icon="🕷️")

# --- 核心：爬蟲功能 (抓取 Lotto-8 網站) ---
@st.cache_data(ttl=3600) # 設定快取 1 小時，避免一直重抓被封鎖
def scrape_lotto_data():
    try:
        # 目標網址：lotto-8 (台灣常見的樂透資料網)
        url = "https://www.lotto-8.com/listlto649.asp"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # 處理編碼 (大部份台灣舊網站是 Big5 或 UTF-8)
        response.encoding = 'utf-8' 
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找尋表格 (lotto-8 的號碼通常在 td 裡面，需要一點特徵判斷)
        # 這裡的邏輯是直接抓取網頁中所有呈現 "數字,數字,數字" 格式的文字
        numbers_data = []
        
        # 抓取表格列 (通常是 tr)
        rows = soup.find_all('tr')
        for row in rows:
            text = row.get_text(strip=True)
            # 簡單過濾：如果這一行有日期且有逗號分隔的數字，就很可能是資料
            # Lotto-8 的格式通常是：期數 日期 號碼1,號碼2...
            if ',' in text and len(text.split(',')) >= 6:
                # 嘗試清理出數字
                # 這裡做簡單處理：把所有非數字的字元清掉，只留數字
                import re
                nums = re.findall(r'\d+', text)
                
                # 大樂透會有 6 個號碼 + 1 個特別號 + 期數 + 日期，所以至少要抓到 7 個數字
                # 過濾掉開頭的期數(例如 113000001) 和日期
                # 我們假設最後面的 7 個數字就是開獎號碼 (由小排到大通常是前6個)
                if len(nums) >= 7:
                    # 取最後 7 碼 (6個平碼 + 1個特別號)
                    draw_nums = [int(n) for n in nums[-7:-1]] # 只取前6個平碼做分析
                    # 過濾掉怪怪的數字 (大樂透只有 1-49)
                    if all(1 <= n <= 49 for n in draw_nums):
                        numbers_data.extend(draw_nums)

        if len(numbers_data) < 10:
            raise Exception("抓到的資料太少，可能網站改版了")

        st.toast("✅ 成功從網路抓取最新資料！", icon="🎉")
        return numbers_data

    except Exception as e:
        st.error(f"爬蟲出了一點小問題 ({e})，目前切換為模擬資料模式。")
        # 備案：如果爬蟲失敗，回傳模擬數據
        mock_data = []
        for _ in range(200):
            mock_data.extend(random.sample(range(1, 50), 6))
        return mock_data

# --- 分析與介面 ---
def analyze_numbers(data):
    df = pd.DataFrame(data, columns=['number'])
    counts = df['number'].value_counts().sort_index()
    for i in range(1, 50):
        if i not in counts.index:
            counts[i] = 0
    return counts.sort_index()

def generate_lucky_numbers(hot_numbers, method='random'):
    if method == 'random':
        return sorted(random.sample(range(1, 50), 6))
    elif method == 'hot':
        # 簡單加權：出現次數越多，權重越高
        weights = hot_numbers.values
        numbers = hot_numbers.index.tolist()
        return sorted(random.choices(numbers, weights=weights, k=6))

# UI 佈局
st.title("🕷️ 2026 大樂透分析 (連線版)")
st.caption("資料來源：第三方樂透網 (即時爬蟲)")

# 側邊欄
st.sidebar.header("設定")
analysis_mode = st.sidebar.radio("選號策略", ["完全隨機", "熱門號碼加權"])

# 執行爬蟲
with st.spinner('正在連線抓取最新開獎資料...'):
    raw_data = scrape_lotto_data()

# 顯示數據量
st.sidebar.markdown(f"📊 目前分析樣本數：**{len(raw_data)//6}** 期")

# 分析
frequency = analyze_numbers(raw_data)

# 圖表
st.subheader("📊 號碼出現頻率 (熱度圖)")
st.bar_chart(frequency, color="#FF4B4B")

# 熱門排行
top_5 = frequency.sort_values(ascending=False).head(5).index.tolist()
bottom_5 = frequency.sort_values(ascending=True).head(5).index.tolist()

col1, col2 = st.columns(2)
with col1:
    st.info(f"🔥 最熱門：{top_5}")
with col2:
    st.warning(f"❄️ 最冷門：{bottom_5}")

# 產生號碼
st.divider()
if st.button("🎲 產生一組號碼", type="primary"):
    mode = 'hot' if "熱門" in analysis_mode else 'random'
    lucky_nums = generate_lucky_numbers(frequency, mode)
    
    st.success("您的推薦號碼：")
    st.markdown(f"## {lucky_nums}")
    
    # 趣味分析
    match_count = sum([1 for n in lucky_nums if n in top_5])
    if match_count >= 2:
        st.caption(f"包含 {match_count} 個熱門號碼，感覺很有機會喔！")
