import streamlit as st
import sqlite3
import pandas as pd
import os

db_path = os.path.join(os.path.expanduser("~"), "inventory.db")
st.set_page_config(page_title="三合MES PRO", layout="wide")

def get_db(): return sqlite3.connect(db_path)

# --- 模組：五金配件 ---
def show_inventory_list():
    st.header("📋 庫存總表")
    conn = get_db()
    try:
        # 使用簡單查詢，避免複雜 JOIN 導致的 SQL 錯誤
        df = pd.read_sql_query("SELECT item_name, category, stock_level, unit, supplier, price FROM items WHERE category IN ('五金配件', '螺絲鐵件')", conn)
        st.dataframe(df.rename(columns={
            'item_name': '零件名稱', 'category': '分類', 'stock_level': '庫存數量', 
            'unit': '單位', 'supplier': '供應商', 'price': '單價'
        }), use_container_width=True)
        
        st.subheader("🔍 查看歷史紀錄")
        item_list = df['item_name'].tolist()
        selected_name = st.selectbox("選擇零件", item_list)
        
        # 查詢紀錄時改用名稱比對，避免 RFID 關聯導致錯誤
        history_df = pd.read_sql_query(
            "SELECT timestamp, txn_type, quantity FROM transactions WHERE rfid_tag = (SELECT rfid_tag FROM items WHERE item_name = ? LIMIT 1) ORDER BY timestamp DESC", 
            conn, params=(selected_name,)
        )
        if not history_df.empty:
            st.table(history_df.rename(columns={'timestamp': '時間', 'txn_type': '類型', 'quantity': '數量'}))
        else:
            st.info("暫無此零件交易紀錄。")
    except Exception as e:
        st.error(f"系統錯誤: {e}")
    conn.close()

# --- 模組：零件入庫 ---
def show_parts_inbound():
    st.header("📥 零件入庫")
    conn = get_db()
    items = pd.read_sql_query("SELECT item_name, unit FROM items WHERE category IN ('五金配件', '螺絲鐵件')", conn)
    item_list = items['item_name'].tolist()
    conn.close()
    
    with st.form("inbound_form"):
        name = st.selectbox("選擇零件", item_list)
        qty = st.number_input("入庫數量", min_value=0.0, step=0.1)
        if st.form_submit_button("執行入庫"):
            conn = get_db()
            conn.execute("UPDATE items SET stock_level = stock_level + ? WHERE item_name = ?", (qty, name))
            conn.execute("INSERT INTO transactions (rfid_tag, txn_type, quantity) SELECT rfid_tag, 'IN', ? FROM items WHERE item_name = ?", (qty, name))
            conn.commit(); conn.close(); st.success("成功"); st.rerun()

# --- 模組：新增零件 ---
def show_add_new_part():
    st.header("➕ 新增零件")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("零件名稱")
        cat = st.selectbox("分類", ["五金配件", "螺絲鐵件"])
        if st.form_submit_button("新增"):
            conn = get_db()
            conn.execute("INSERT INTO items (item_name, category, stock_level) VALUES (?, ?, 0)", (name, cat))
            conn.commit(); conn.close(); st.success("新增成功"); st.rerun()

# --- 主控制台 ---
with st.sidebar:
    st.title("三合 MES PRO")
    main_menu = st.radio("導覽列", ["🛠️ 派工系統", "🔩 五金螺絲庫存", "🏗️ 鋁料專區"])
    sub_menu = st.radio("子目錄", ["庫存總表", "零件入庫", "新增零件"]) if main_menu == "🔩 五金螺絲庫存" else None

if main_menu == "🛠️ 派工系統": st.header("🛠️ 派工管理")
elif main_menu == "🏗️ 鋁料專區": st.header("🏗️ 鋁料管理")
elif main_menu == "🔩 五金螺絲庫存":
    if sub_menu == "庫存總表": show_inventory_list()
    elif sub_menu == "零件入庫": show_parts_inbound()
    elif sub_menu == "新增零件": show_add_new_part()
