import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt

# 設定網頁標題與圖示
st.set_page_config(page_title="2026 大樂透財富密碼", page_icon="💰")

# --- 1. 模擬數據區 (之後可以用爬蟲取代) ---
@st.cache_data
def load_data():
    # 這裡我們先模擬過去 100 期的開獎號碼 (1-49號)
    # 真實情況：您可以寫一個爬蟲抓取台灣彩券官網
    data = []
    for _ in range(100):
        draw = random.sample(range(1, 50), 6) # 大樂透是 49 選 6
        data.extend(draw)
    return data

# --- 2. 核心邏輯區 ---
def analyze_numbers(data):
    df = pd.DataFrame(data, columns=['number'])
    # 計算每個號碼出現的次數
    counts = df['number'].value_counts().sort_index()
    # 補齊沒出現過的號碼 (確保 1-49 都有)
    for i in range(1, 50):
        if i not in counts.index:
            counts[i] = 0
    return counts.sort_index()

def generate_lucky_numbers(hot_numbers, method='random'):
    if method == 'random':
        return sorted(random.sample(range(1, 50), 6))
    elif method == 'hot':
        # 權重選號：熱門號碼中獎機率較高 (這裡只是簡單邏輯)
        weights = hot_numbers.values
        numbers = hot_numbers.index.tolist()
        return sorted(random.choices(numbers, weights=weights, k=6))

# --- 3. 介面設計 (UI) ---
st.title("🧧 2026 新春大樂透 - 財富密碼分析器")
st.markdown("不用去廟裡求，用 **大數據** 幫你算！")

# 側邊欄：功能選單
st.sidebar.header("功能設定")
analysis_mode = st.sidebar.radio("選擇選號模式", ["完全隨機 (聽天由命)", "熱門號碼加權 (數據流)"])

# 載入數據
history_data = load_data()
frequency = analyze_numbers(history_data)

# 顯示熱門號碼圖表
st.subheader("📊 過去 100 期號碼出現頻率")
st.bar_chart(frequency)

# 找出最熱門的前 5 名
top_5 = frequency.sort_values(ascending=False).head(5).index.tolist()
st.info(f"🔥 近期最熱門號碼 Top 5：{top_5}")

# 產生按鈕
st.divider()
st.subheader("👇 點擊下方按鈕產生你的發財號碼")

if st.button("✨ 產生本期幸運號碼 ✨", type="primary"):
    mode = 'hot' if "熱門" in analysis_mode else 'random'
    lucky_nums = generate_lucky_numbers(frequency, mode)
    
    # 顯示結果 (用大字體)
    st.success(f"您的幸運號碼是：")
    st.markdown(f"## {lucky_nums}")
    st.caption("僅供參考，投資理財請量力而為！")

# --- 賺錢的小心機 (廣告位) ---
st.divider()
st.markdown("---")
st.markdown("💡 **覺得準嗎？分享給朋友一起做公益！**")
# 這裡未來可以放您的 Google AdSense 廣告程式碼，或是導購連結
