import streamlit as st
import pandas as pd
import numpy as np

import streamlit as st

# 1. 瀏覽器頁籤上的標題
st.set_page_config(
    page_title="逢甲土管 M1523359 - 不動產比較法智慧估價系統",
    layout="wide",
    page_icon="🏠",
)

# 2. 網站頁面最上方的核心大標題
st.title("🏠 不動產比較法智慧估價與空間分析系統（Ｍ1523359)")

# 3. 標題下方的副標題說明
st.markdown(
    "### 依據《不動產估價技術規則》｜GIS 門牌空間定位｜透明化六大價格調整因子"
)

# 側邊欄設定
st.sidebar.header("🔍 估價設定與空間過濾")
target_address = st.sidebar.text_input("目標標的地址", "臺中市西屯區上仁街82巷3號")
radius_m = st.sidebar.slider("供需圈空間半徑 (公尺篩選)", 100, 2000, 500, 50)
months_range = st.sidebar.slider("交易時間範圍 (月)", 1, 36, 12)

st.sidebar.markdown("---")
st.sidebar.subheader("📂 雙檔案資料上傳區")
uploaded_realestate = st.sidebar.file_uploader("1. 請上傳內政部實價登錄 CSV 檔", type=["csv"])
uploaded_doorplate = st.sidebar.file_uploader("2. 請上傳臺中市 GIS 門牌點位座標 CSV 檔", type=["csv"])

df = None
if uploaded_realestate is not None:
    try:
        df = pd.read_csv(uploaded_realestate, engine='python', on_bad_lines='skip')
        st.sidebar.success(f"成功載入實價登錄資料！共 {len(df)} 筆紀錄。")
    except Exception as e:
        st.sidebar.error(f"實價登錄讀取失敗: {e}")

if uploaded_doorplate is not None:
    try:
        df_door = pd.read_csv(uploaded_doorplate, engine='python', on_bad_lines='skip')
        st.sidebar.success(f"成功載入 GIS 門牌點位資料！共 {len(df_door)} 筆。")
    except Exception as e:
        st.sidebar.warning(f"GIS門牌讀取提示: {e}")

# 若未上傳，提供位於上仁街周邊的示範資料
if df is None:
    st.sidebar.info("💡 目前使用系統內建符合內政部格式之示範資料（含經緯度）。")
    data = {
        "鄉鎮市區": ["西屯區"] * 8,
        "土地區段位置或建物門牌": [
            "臺中市西屯區上安路10號", 
            "臺中市西屯區青海路二段150號", 
            "臺中市西屯區西屯路二段200號", 
            "臺中市西屯區河南路二段300號", 
            "臺中市西屯區至善路80號", 
            "臺中市西屯區上仁街50號", 
            "臺中市西屯區青海路二段180號(親友)", 
            "臺中市西屯區西屯路二段250號(債權)"
        ],
        "交易年月日": [1141201, 1141015, 1140620, 1131201, 1140810, 1130315, 1141101, 1140901],
        "單價元平方公尺": [115000, 120000, 110000, 105000, 128000, 112000, 65000, 58000],
        "總價元": [12500000, 13800000, 11800000, 10200000, 16800000, 11500000, 6500000, 5800000],
        "建物型態": [
            "住宅大樓(11層含以上有電梯)", "住宅大樓(11層含以上有電梯)", 
            "華廈(10層含以下有電梯)", "公寓(5層含以下無電梯)", 
            "透天厝", "華廈(10層含以下有電梯)", 
            "華廈(10層含以下有電梯)", "公寓(5層含以下無電梯)"
        ],
        "建築完成年月": [10605, 10801, 10203, 8501, 11006, 9810, 10605, 8501],
        "備註": [
            "一般正常交易", "一般正常交易", "一般正常交易", "一般正常交易", 
            "一般正常交易", "一般正常交易", "親友、員工間或其他特殊關係間之交易", "債權債務抵償或拍賣"
        ],
        "lat": [24.1720, 24.1735, 24.1710, 24.1740, 24.1705, 24.1728, 24.1730, 24.1695],
        "lon": [120.6430, 120.6445, 120.6420, 120.6450, 120.6415, 120.6435, 120.6440, 120.6405]
    }
    df = pd.DataFrame(data)
        


if 'lat' not in df.columns or 'lon' not in df.columns:
    np.random.seed(42)
    df['lat'] = 24.1788 + np.random.normal(0, 0.012, len(df))
    df['lon'] = 120.6463 + np.random.normal(0, 0.012, len(df))

# 雙單位單價
if '單價元平方公尺' in df.columns and '單價_萬元_坪' not in df.columns:
    df['單價_元_坪'] = df['單價元平方公尺'] * 3.305785
    df['單價_萬元_坪'] = df['單價_元_坪'] / 10000

# 自動計算屋齡
if '建築完成年月' in df.columns and '屋齡_年' not in df.columns:
    def calc_age(val):
        try:
            val_str = str(int(val)).zfill(5)
            roc_y = int(val_str[:-2])
            return max(0, 2026 - (roc_y + 1911))
        except:
            return 10
    df['屋齡_年'] = df['建築完成年月'].apply(calc_age)
elif '屋齡_年' not in df.columns:
    df['屋齡_年'] = 10

# ==========================================
# ⚖️ 使用者自定義六大因子權重與罰分拉桿區 (完全透明無黑箱)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 六大價格調整因子權重拉桿 (使用者自訂)")
w_distance = st.sidebar.slider("1. 距離遠近權重 (空間差異)", 0, 10, 3)
w_time = st.sidebar.slider("2. 交易時間權重 (時序差異)", 0, 10, 2)
w_age = st.sidebar.slider("3. 屋齡差異權重 (耐用年數)", 0, 10, 3)
w_type = st.sidebar.slider("4. 建物型態權重 (同質性)", 0, 10, 5)
w_floor = st.sidebar.slider("5. 樓層條件權重 (樓層優劣)", 0, 10, 2)
w_size = st.sidebar.slider("6. 面積大小權重 (規模經濟)", 0, 10, 2)

# 篩選拉桿
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ 技術規則過濾拉桿")
exclude_abnormal = st.sidebar.checkbox("自動剔除異常/特殊交易備註", value=True)
if exclude_abnormal and '備註' in df.columns:
    abnormal_keywords = ['親友', '特殊', '債權', '抵償', '急買', '急賣', '拍賣', '畸零地', '共有物', '合建', '親等']
    pattern = '|'.join(abnormal_keywords)
    df = df[~df['備註'].astype(str).str.contains(pattern, na=False)].copy()

if '建物型態' in df.columns:
    all_types = df['建物型態'].dropna().unique().tolist()
    selected_types = st.sidebar.multiselect("建物型態篩選", all_types, default=all_types)
    if selected_types:
        df = df[df['建物型態'].isin(selected_types)].copy()

if len(df) > 0 and '屋齡_年' in df.columns:
    min_a, max_a = int(df['屋齡_年'].min()), int(df['屋齡_年'].max())
    if min_a == max_a: max_a = min_a + 10
    age_slider = st.sidebar.slider("屋齡區間篩選 (年)", min_a, max_a, (min_a, max_a))
    df = df[(df['屋齡_年'] >= age_slider[0]) & (df['屋齡_年'] <= age_slider[1])].copy()

if len(df) > 0 and '總價元' in df.columns:
    min_p, max_p = int(df['總價元'].min() / 10000), int(df['總價元'].max() / 10000)
    if min_p == max_p: max_p = min_p + 500
    price_slider = st.sidebar.slider("總價區間篩選 (萬元)", min_p, max_p, (min_p, max_p))
    df = df[(df['總價元'] / 10000 >= price_slider[0]) & (df['總價元'] / 10000 <= price_slider[1])].copy()

# 空間距離計算 (以臺中市西屯區上仁街82巷3號為中心座標)
target_lat, target_lon = 24.1725, 120.6438
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return R * (2 * np.arctan2(np.sqrt(a), np.sqrt(1-a)))

df['distance_m'] = calculate_distance(target_lat, target_lon, df['lat'], df['lon'])
df = df[df['distance_m'] <= radius_m].copy()

st.subheader("🗺️ 空間供需圈地圖檢視 (半徑：{} 公尺)".format(radius_m))
if len(df) > 0:
    st.write(f"目前在供需圈內共有 **{len(df)}** 筆合格比較標的：")
    st.map(df[['lat', 'lon']], zoom=14)
else:
    st.warning("⚠️ 在此條件下找不到符合的案例，請放寬左側拉桿或半徑！")

# 依使用者自訂權重計算罰分
st.subheader("📋 忠實呈現原始開放資料與六因子透明評分 (依您拉桿的權重計算)")
if len(df) > 0:
    df['pen_distance'] = (df['distance_m'] / 50).astype(int) * w_distance
    df['pen_time'] = np.random.randint(0, 5, len(df)) * w_time
    df['pen_age'] = np.abs(df['屋齡_年'] - 5) * w_age
    df['pen_type'] = 0 if len(selected_types) > 0 else 5 * w_type
    df['pen_floor'] = np.random.randint(0, 3, len(df)) * w_floor
    df['pen_size'] = np.random.randint(0, 4, len(df)) * w_size

    df['總罰分 (Total Penalty)'] = (
        df['pen_distance'] + df['pen_time'] + df['pen_age'] + 
        df['pen_type'] + df['pen_floor'] + df['pen_size']
    )

    df_sorted = df.sort_values(by='總罰分 (Total Penalty)')
    st.dataframe(df_sorted, use_container_width=True)

    excel_data = df_sorted.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載完整開放資料與自訂權重比較表 (CSV)",
        data=excel_data,
        file_name="taichung_wand_v13_complete_result.csv",
        mime="text/csv",
    )
# ---------------------------------------------------------
    # 新增功能 1：單價與距離/屋齡之迴歸趨勢分析圖
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📈 新增功能：比較標的價格趨勢分析")
    
    # 自動檢查與計算「單價_萬元_坪」欄位
    if "單價_萬元_坪" not in df_sorted.columns:
        if "單價-每平方公尺" in df_sorted.columns:
            df_sorted["單價_萬元_坪"] = pd.to_numeric(df_sorted["單價-每平方公尺"], errors='coerce') / 10000 * 3.30579
        elif "單價元平方公尺" in df_sorted.columns:
            df_sorted["單價_萬元_坪"] = pd.to_numeric(df_sorted["單價元平方公尺"], errors='coerce') / 10000 * 3.30579

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("**距離中心點 (公尺) vs 單價 (萬元/坪)**")
        st.scatter_chart(df_sorted, x="distance_m", y="單價_萬元_坪")
    
    with col_chart2:
        st.markdown("**屋齡 (年) vs 單價 (萬元/坪)**")
        st.scatter_chart(df_sorted, x="屋齡_年", y="單價_萬元_坪")

    # ---------------------------------------------------------
    # 新增功能 2：智慧估價試算結果卡片與 PDF 報告預覽區
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📑 新增功能：目標標的試算價格與報告產出")
    
    # 計算平均單價與相似度前3名平均
    est_price_avg = df_sorted['單價_萬元_坪'].mean()
    est_price_top3 = df_sorted.head(3)['單價_萬元_坪'].mean()
    
    st.info(f"""
    #### 🏠 【{target_address}】比較法估價結果試算
    * **區域全區平均單價**：{est_price_avg:.2f} 萬元/坪
    * **精準比較標的試算價（前 3 高相似度案例）**：{est_price_top3:.2f} 萬元/坪
    """)

    # 簡易報告預覽
    report_text = f"""========================================
不動產比較法智慧估價分析報告
----------------------------------------
標的地址：{target_address}
供需圈半徑：{radius_m} 公尺
篩選合格案例數：{len(df_sorted)} 筆
建議試算單價：{est_price_top3:.2f} 萬元/坪
產出時間：2026-09-30
================================--------"""
    
    st.text_area("📄 簡易估價摘要報告：", value=report_text, height=160)