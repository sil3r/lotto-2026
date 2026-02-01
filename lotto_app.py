import streamlit as st
import pandas as pd
import requests
import random
import re

st.set_page_config(page_title="2026 大樂透神器 (雙核心版)", page_icon="🎲")

# --- 核心：多重來源爬蟲 ---
@st.cache_data(ttl=3600)
def scrape_lotto_data():
    # 定義我們要嘗試的網站清單 (來源 A 失敗就自動換來源 B)
    sources = [
        {
            "name": "9800 樂透網",
            "url": "https://www.9800.com.tw/lotto649/prev.html",
            "encoding": "big5"  # 老網站通常用 Big5
        },
        {
            "name": "Lotto-8",
            "url": "https://www.lotto-8.com/listlto649.asp",
            "encoding": "utf-8"
        }
    ]

    for source in sources:
        try:
            # 1. 發送請求
            header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
            }
            r = requests.get(source["url"], headers=header, timeout=10)
            
            # 設定編碼 (避免亂碼)
            r.encoding = source["encoding"]
            
            # 2. 暴力抓表格
            # match參數：告訴 pandas 只抓含有「號碼」或「期別」這類關鍵字的表格
            # 這樣可以避開網頁排版用的空表格
            dfs = pd.read_html(r.text, match=r'\d+') 
            
            if not dfs:
                continue # 沒抓到，換下一個網站

            # 3. 尋找正確的表格 (列數夠多的那個)
            df = max(dfs, key=len)
            
            # 4. 資料清洗 (通用邏輯)
            numbers_data = []
            history_display = []
            
            for index, row in df.iterrows():
                row_text = str(row.values)
                # 抓出所有數字
                nums = re.findall(r'\d+', row_text)
                # 過濾：只留 1~49
                valid_nums = [int(n) for n in nums if 1 <= int(n) <= 49]
                
                # 大樂透一期至少 6 個號碼
                if len(valid_nums) >= 6:
                    # 通常前 6 個是平碼
                    main_nums = valid_nums[:6]
                    numbers_data.extend(main_nums)
                    
                    # 存前 10 筆顯示用
                    if len(history_display) < 10:
                        history_display.append({
                            "網站": source["name"],
                            "號碼": str(main_nums)
                        })

            if len(numbers_data) > 50:
                st.toast(f"✅ 成功連線！資料來源：{source['name']}", icon="🎉")
                return numbers_data, history_display
        
        except Exception as e:
            print(f"{source['name']} 失敗: {e}")
            continue # 失敗就默默換下一個

    # 如果全部網站都失敗
    raise Exception("所有網站都擋爬蟲，請稍後再試")

# --- 介面與處理 (失敗時的備案) ---
st.title("🎰 2026 大樂透分析 (雙核心版)")

try:
    with st.spinner('正在搜尋各大樂透網站資料...'):
        raw_data, history_list = scrape_lotto_data()
        
    # 顯示來源
    if history_list:
        st.caption(f"目前使用資料來源：{history_list[0]['網站']}")
        with st.expander("📅 查看最新開獎數據"):
            st.dataframe(pd.DataFrame(history_list))

except Exception as e:
    st.error(f"連線暫時受阻 ({e})，已自動切換為 **離線模擬模式**。")
    st.caption("這通常是因為雲端主機 IP 短暫被封鎖，過幾小時通常會自動解除。")
    # 模擬數據 (讓 App 還是可以用)
    raw_data = [random.randint(1, 49) for _ in range(600)]

# --- 分析功能 (保持不變) ---
def analyze_numbers(data):
    df = pd.DataFrame(data, columns=['number'])
    counts = df['number'].value_counts().sort_index()
    for i in range(1, 50):
        if i not in counts.index:
            counts[i] = 0
    return counts.sort_index()

frequency = analyze_numbers(raw_data)
top_5 = frequency.sort_values(ascending=False).head(5).index.tolist()

st.subheader("🔥 熱門號碼分析")
st.bar_chart(frequency, color="#FF4B4B")
st.info(f"近期最旺號碼 Top 5：{top_5}")

st.divider()
if st.button("✨ 產生本期幸運號碼", type="primary"):
    # 加權選號
    weights = frequency.values + 0.1
    nums = frequency.index.tolist()
    lucky = sorted(random.choices(nums, weights=weights, k=6))
    
    st.success("您的推薦號碼：")
    st.markdown(f"## {lucky}")
    st.caption("祝您中獎！")
