import streamlit as st
import pandas as pd
import requests
import random

# 設定網頁標題
st.set_page_config(page_title="2026 大樂透神器 (穩定爬蟲版)", page_icon="💰")

# --- 核心：爬蟲功能 (針對 Lotto-8 網站) ---
@st.cache_data(ttl=3600) # 1小時更新一次即可
def scrape_lotto_data():
    try:
        # Lotto-8 的大樂透歷史資料頁面
        url = "https://www.lotto-8.com/listlto649.asp"
        
        # 偽裝成一般瀏覽器
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # 抓取網頁
        r = requests.get(url, headers=header)
        r.encoding = 'utf-8' # 設定編碼
        
        # 關鍵大招：Pandas 自動尋找網頁裡的所有表格
        dfs = pd.read_html(r.text)
        
        # 邏輯：我們要找「列數最多」的那個表格，通常就是歷史資料表
        df = max(dfs, key=len)
        
        # 資料清洗
        numbers_data = []
        history_display = []
        
        # 逐行檢查
        import re
        for index, row in df.iterrows():
            row_text = str(row.values)
            # 抓出這一行裡所有的數字
            nums = re.findall(r'\d+', row_text)
            # 過濾：只留 1~49 的數字
            valid_nums = [int(n) for n in nums if 1 <= int(n) <= 49]
            
            # 一期大樂透通常會有 6個平碼 + 1個特別號，所以至少要有 7 個數字
            if len(valid_nums) >= 6:
                # 前 6 個通常是平碼 (由小排到大)
                main_nums = valid_nums[:6]
                numbers_data.extend(main_nums)
                
                # 順便存一下要顯示給使用者看的列表 (只存最近 10 筆)
                if len(history_display) < 10:
                    history_display.append({
                        "開獎號碼": str(main_nums),
                        "來源": "Lotto-8"
                    })

        if len(numbers_data) < 50:
             raise Exception("抓到的資料太少")

        st.toast(f"✅ 成功從 Lotto-8 抓取資料！", icon="🎉")
        return numbers_data, history_display

    except Exception as e:
        st.error(f"連線失敗 ({e})，目前顯示模擬資料。")
        # 備案模擬資料
        return [random.randint(1, 49) for _ in range(600)], []

# --- 介面區 ---
st.title("🎰 2026 大樂透分析 (穩定連線版)")
st.caption("資料來源：Lotto-8 資訊網 (HTML 解析)")

with st.spinner('正在連線抓取...'):
    raw_data, history_list = scrape_lotto_data()

# 顯示最新的開獎列表
if history_list:
    with st.expander("📅 查看最新開獎號碼 (來自 Lotto-8)"):
        st.dataframe(pd.DataFrame(history_list))

# 分析邏輯
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
        weights = hot_numbers.values
        numbers = hot_numbers.index.tolist()
        return sorted(random.choices(numbers, weights=weights, k=6))

# 顯示前幾名的熱門號
frequency = analyze_numbers(raw_data)
top_5 = frequency.sort_values(ascending=False).head(5).index.tolist()

st.subheader("🔥 近期最熱門號碼")
st.info(f"Top 5：{top_5}")

st.bar_chart(frequency, color="#FF4B4B")

st.divider()
if st.button("✨ 產生本期幸運號碼 ✨", type="primary"):
    lucky = generate_lucky_numbers(frequency, 'hot')
    st.success("您的財富密碼：")
    st.markdown(f"## {lucky}")
    st.caption("祝您中大獎！")
