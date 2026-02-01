import streamlit as st
import pandas as pd
import requests
import random
import urllib3

# 1. 忽略不安全連線警告 (解決紅字問題)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設定網頁標題
st.set_page_config(page_title="2026 台彩官方 API 分析器", page_icon="🇹🇼")

# --- 核心：直攻台彩官方 API (修正憑證問題版) ---
@st.cache_data(ttl=300) # 5分鐘更新一次
def fetch_official_lottery_data():
    try:
        # 這是台彩新官網背後真正的 API 網址
        api_url = "https://api.taiwanlottery.com/TLCAPIWechat/Lottery/SuperLotto649/Result"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://www.taiwanlottery.com",
            "Referer": "https://www.taiwanlottery.com/"
        }
        
        # 關鍵修改：加上 verify=False (忽略憑證檢查)
        response = requests.get(api_url, headers=headers, timeout=10, verify=False)
        
        if response.status_code != 200:
            raise Exception(f"API 回傳錯誤碼: {response.status_code}")
            
        data_json = response.json()
        
        if 'content' not in data_json or 'superLotto649Res' not in data_json['content']:
             raise Exception("API 資料結構改變，無法讀取")

        raw_list = data_json['content']['superLotto649Res']
        
        numbers_data = []
        history_display = []
        
        for item in raw_list:
            nums = item.get('drawNumberSize', [])
            term = item.get('drawTerm', '未知')
            date = item.get('drawDate', '未知')
            
            if len(nums) >= 6:
                main_nums = [int(n) for n in nums[:6]]
                special_num = int(nums[6]) if len(nums) > 6 else 0
                
                numbers_data.extend(main_nums)
                
                history_display.append({
                    "期數": term,
                    "日期": date.split('T')[0],
                    "號碼": str(main_nums),
                    "特別號": special_num
                })

        st.toast("✅ 成功連線台彩官方 API！", icon="🇹🇼")
        return numbers_data, history_display

    except Exception as e:
        # 如果失敗，印出錯誤訊息在畫面上方便除錯
        st.error(f"連線官方 API 失敗 ({e})，切換回模擬模式。")
        # 備用模擬資料
        return [random.randint(1, 49) for _ in range(60)], []

# --- 介面區 ---
st.title("🇹🇼 2026 大樂透 - 台彩官方連線版")
st.caption("資料來源：api.taiwanlottery.com (官方即時數據)")

with st.spinner('正在呼叫台彩 API...'):
    raw_data, history_list = fetch_official_lottery_data()

# 顯示最新的開獎列表
if history_list:
    with st.expander("📅 查看最近 10 期開獎清單 (點擊展開)"):
        st.dataframe(pd.DataFrame(history_list))

# 分析邏輯
def analyze_numbers(data):
    df = pd.DataFrame(data, columns=['number'])
    counts = df['number'].value_counts().sort_index()
    for i in range(1, 50): # 補齊 1-49
        if i not in counts.index:
            counts[i] = 0
    return counts.sort_index()

frequency = analyze_numbers(raw_data)

# 熱門號碼圖表
st.subheader("📊 近期號碼熱度分析")
st.bar_chart(frequency, color="#00C49F") 

# 產生幸運號
st.divider()
if st.button("💰 根據官方數據產生幸運號碼", type="primary"):
    weights = frequency.values
    numbers = frequency.index.tolist()
    # 避免權重為 0
    weights = [w + 0.1 for w in weights]
    
    lucky = sorted(random.choices(numbers, weights=weights, k=6))
    
    st.success("您的財富密碼：")
    st.markdown(f"## {lucky}")
    st.caption("資料來源：台灣彩券官方 API")
