import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="ระบบบันทึกวันลาครู 2569", layout="wide")

# --- เชื่อมต่อ Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)

# ดึงรายชื่อครู (ปรับเปลี่ยนชื่อได้ที่นี่)
TEACHERS = ["ครูสมชาย", "ครูสมศรี", "ครูนภา", "ครูวันชัย", "ครูเกียรติศักดิ์"]

st.title("🗓️ ระบบบันทึกรายชื่อการลาครู ปี 2569")

# --- ส่วนสรุปผล (Sidebar) ---
st.sidebar.header("📊 สรุปยอดลาประจำเดือน")
data = conn.read(worksheet="Sheet1", ttl=0) # อ่านข้อมูลสดๆ

if not data.empty:
    # กรองเฉพาะคนที่ลาจริง (ไม่รวมมาปกติ)
    leave_data = data[data['Leave_Type'] != "มาปกติ"]
    if not leave_data.empty:
        summary = leave_data.groupby(['Teacher_Name', 'Leave_Type']).size().unstack(fill_value=0)
        st.sidebar.dataframe(summary)
    else:
        st.sidebar.write("ยังไม่มีประวัติการลา")

# --- ส่วนปฏิทินเลือกวัน ---
month_names = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
               "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
sel_month = st.selectbox("เลือกเดือน", range(1, 13), format_func=lambda x: month_names[x-1])

st.write(f"### เลือกวันที่ในเดือน {month_names[sel_month-1]} 2569")

# สร้างปุ่มวันที่ 1-31 (แบบง่าย)
cols = st.columns(7)
for day in range(1, 32):
    try:
        current_date = datetime.date(2026, sel_month, day)
        with cols[(day-1)%7]:
            if st.button(f"{day}", key=f"d_{day}", use_container_width=True):
                st.session_state.selected_date = current_date.strftime("%Y-%m-%d")
    except ValueError:
        pass # วันที่ไม่มีจริง เช่น 31 กุมภาพันธ์

# --- ส่วนแบบฟอร์มบันทึกข้อมูล ---
if 'selected_date' in st.session_state:
    sel_date = st.session_state.selected_date
    st.divider()
    st.subheader(f"📝 บันทึกการลาวันที่: {sel_date}")

    with st.form(key="leave_form"):
        updated_rows = []
        for teacher in TEACHERS:
            c1, c2, c3, c4 = st.columns([2, 1, 1, 3])
            c1.write(f"**{teacher}**")
            l_sick = c2.checkbox("ลาป่วย", key=f"s_{teacher}")
            l_pers = c3.checkbox("ลากิจ", key=f"p_{teacher}")
            note = c4.text_input("หมายเหตุ", key=f"n_{teacher}", placeholder="สาเหตุ...")

            status = "มาปกติ"
            if l_sick: status = "ลาป่วย"
            elif l_pers: status = "ลากิจ"

            updated_rows.append({"Date": sel_date, "Teacher_Name": teacher, "Leave_Type": status, "Note": note})

        if st.form_submit_button("💾 บันทึกข้อมูล"):
            # ลบข้อมูลเก่าของวันนั้น (ถ้ามี) แล้วเขียนใหม่
            if not data.empty:
                data = data[data['Date'] != sel_date]
            new_data = pd.concat([data, pd.DataFrame(updated_rows)], ignore_index=True)
            conn.update(worksheet="Sheet1", data=new_data)
            st.success("บันทึกสำเร็จ!")
            st.rerun()