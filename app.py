import streamlit as st
import sqlite3
import pandas as pd
import os
import re

# Cloud Database Path
db_path = "inventory.db" # 直接放在專案根目錄下，Streamlit Cloud 臨時會生效

st.set_page_config(page_title="三合MES PRO", layout="wide")

def get_db():
    conn = sqlite3.connect(db_path)
    # 初始化資料表 (如果不存在)
    conn.execute('''CREATE TABLE IF NOT EXISTS items 
                   (item_id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT UNIQUE, 
                    category TEXT, stock_level REAL, unit TEXT, supplier TEXT, price REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS work_orders 
                   (wo_id INTEGER PRIMARY KEY AUTOINCREMENT, technician_name TEXT, 
                    customer_name TEXT, description TEXT, status TEXT DEFAULT '待處理', timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS transactions 
                   (txn_id INTEGER PRIMARY KEY AUTOINCREMENT, rfid_tag TEXT, txn_type TEXT, quantity REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn

# --- 圖片顯示 ---
img_folder = "images"
def display_item_image(name):
    numbers = re.findall(r'\d+', name)
    if numbers:
        rfid = numbers[-1]
        if os.path.exists(img_folder):
            matching_imgs = [f for f in os.listdir(img_folder) if f.startswith(f"{rfid}.")]
            if matching_imgs:
                st.image(os.path.join(img_folder, matching_imgs[0]), caption=f"規格圖: {name}", width=400)

# --- 模組 ---
def show_inventory_list():
    st.header("📋 庫存總表")
    conn = get_db()
    df = pd.read_sql_query("SELECT item_name, category, stock_level, unit, supplier, price FROM items WHERE category IN ('五金配件', '螺絲鐵件')", conn)
    st.dataframe(df, use_container_width=True)
    conn.close()

def show_parts_inbound():
    st.header("📥 零件入庫")
    conn = get_db()
    df_items = pd.read_sql_query("SELECT item_name, unit FROM items", conn)
    conn.close()
    if df_items.empty: st.warning("無資料"); return
    
    with st.form("inbound_form"):
        name = st.selectbox("零件", df_items['item_name'].tolist())
        qty = st.number_input("數量", min_value=0.0)
        if st.form_submit_button("執行"):
            conn = get_db()
            conn.execute("UPDATE items SET stock_level = stock_level + ? WHERE item_name = ?", (qty, name))
            conn.commit(); conn.close(); st.rerun()

def show_add_new_part():
    st.header("➕ 新增零件")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("名稱")
        cat = st.selectbox("分類", ["五金配件", "螺絲鐵件"])
        if st.form_submit_button("新增"):
            conn = get_db()
            conn.execute("INSERT INTO items (item_name, category, stock_level) VALUES (?, ?, 0)", (name, cat))
            conn.commit(); conn.close(); st.success("新增成功"); st.rerun()

# --- 路由 ---
with st.sidebar:
    st.title("三合 MES PRO")
    main = st.radio("導覽列", ["🛠️ 派工", "🔩 五金螺絲", "🏗️ 鋁料"])
    sub = st.radio("子目錄", ["庫存總表", "零件入庫", "新增零件"]) if main == "🔩 五金螺絲" else None

if main == "🛠️ 派工": st.header("🛠️ 派工管理")
elif main == "🏗️ 鋁料": st.header("🏗️ 鋁料管理")
elif main == "🔩 五金螺絲":
    if sub == "庫存總表": show_inventory_list()
    elif sub == "零件入庫": show_parts_inbound()
    elif sub == "新增零件": show_add_new_part()
