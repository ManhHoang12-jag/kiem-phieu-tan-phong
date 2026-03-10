import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import time
import base64
import os

# ==========================================
# 1. THIẾT LẬP GIAO DIỆN & CSS (GIỮ NGUYÊN)
# ==========================================
st.set_page_config(page_title="Hệ thống Báo cáo Bầu cử phường Tân Phong", page_icon="🇻🇳", layout="centered")

st.markdown("""
<style>
    #MainMenu, footer, header, .stAppDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
    .block-container {padding-top: 1.5rem !important; max-width: 800px;}
    .stButton>button {width: 100%; font-weight: bold; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KẾT NỐI GOOGLE SHEETS
# ==========================================
@st.cache_resource(show_spinner=False)
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Tên file Google Sheets của bạn
    return client.open("Solieubaucutanphong")

try:
    file_du_lieu = init_connection()
except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.stop()

# ==========================================
# 3. CẤU HÌNH HỆ THỐNG (BẠN SỬA TÊN ĐẠI BIỂU TẠI ĐÂY)
# ==========================================
# Bước 1: Liệt kê danh sách đại biểu theo từng Đơn vị
DANH_SACH_DAI_BIEU = {
    "Đơn vị số 1": ["Đại biểu A", "Đại biểu B", "Đại biểu C"],
    "Đơn vị số 2": ["Đại biểu D", "Đại biểu E"]
}

# Bước 2: TRỎ CỘT CHÍNH XÁC - Đảm bảo tên ở đây giống hệt tên ở Bước 1
# Tôi đã trỏ Đại biểu A vào cột AA như bạn yêu cầu
MAP_COT = {
    "phieu_phat_ra": "M",
    "phieu_thu_vao": "N",
    "phieu_hop_le": "O",
    "phieu_khong_hop_le": "P",
    
    "Đại biểu A": "AA", 
    "Đại biểu B": "AB",
    "Đại biểu C": "AC",
    "Đại biểu D": "AD",
    "Đại biểu E": "AE"
}

# Bước 3: Phân bổ Tổ nào thuộc Đơn vị nào (Tổ 1-23: ĐV1, 24-46: ĐV2)
PHAN_BO_TO = {f"Tổ {i}": "Đơn vị số 1" if i <= 23 else "Đơn vị số 2" for i in range(1, 47)}

# ==========================================
# 4. HEADER & LOGO (GIỮ NGUYÊN)
# ==========================================
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f: encoded_img = base64.b64encode(f.read()).decode()
    img_src = f"data:image/png;base64,{encoded_img}"
else:
    img_src = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Flag_of_Vietnam.svg/200px-Flag_of_Vietnam.svg.png"

header_html = f"""<div style="display: flex; align-items: center; border-bottom: 2px solid #cc0000; padding-bottom: 15px; margin-bottom: 25px;"><img src="{img_src}" width="75" style="margin-right: 15px; flex-shrink: 0;"><div style="flex-grow: 1; overflow: hidden;"><h3 style="margin: 0; color: #cc0000; font-size: clamp(14px, 4vw, 20px); white-space: nowrap;">ỦY BAN NHÂN DÂN PHƯỜNG TÂN PHONG</h3><h5 style="margin: 0; color: #333333; font-size: clamp(12px, 3.5vw, 16px); margin-top: 4px; white-space: nowrap;">Cổng Nhập liệu Bầu cử Trực tuyến</h5></div></div>"""
st.markdown(header_html, unsafe_allow_html=True)

# ==========================================
# 5. XỬ LÝ ĐĂNG NHẬP
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'ten_to': '', 'hang_cua_to': 0})

if not st.session_state['logged_in']:
    with st.form("Login"):
        user = st.selectbox("Chọn Tổ bầu cử:", [f"Tổ {i}" for i in range(1, 47)])
        pwd = st.text_input("Mã bảo mật:", type="password")
        if st.form_submit_button("Đăng nhập"):
            hang = 6 + (int(user.replace("Tổ ", "")) - 1)
            try:
                # Kiểm tra mật khẩu tại cột B (cột 2)
                correct_pwd = file_du_lieu.worksheet("Quoc Hoi").cell(hang, 2).value
                if str(pwd) == str(correct_pwd):
                    st.session_state.update({'logged_in': True, 'ten_to': user, 'hang_cua_to': hang})
                    st.rerun()
                else: st.error("Mã bảo mật sai!")
            except: st.error("Lỗi truy xuất mật khẩu!")
# ==========================================
# 6. PHẦN NHẬP LIỆU TOÀN DIỆN (ĐÃ SỬA LỖI TRỎ CỘT)
# ==========================================
else:
    st.info(f"👤 **{st.session_state['ten_to']}** | 📍 Đơn vị báo cáo: **{PHAN_BO_TO[st.session_state['ten_to']]}**")
    
    with st.form("MainForm"):
        # Phần 1: Cử tri
        st.markdown("#### 🗳️ 1. Tiến độ cử tri đi bầu")
        c1, c2, c3 = st.columns(3)
        with c1: t_ct = st.number_input("Tổng cử tri (J)", min_value=0, step=1)
        with c2: n_ct = st.number_input("Nam (K)", min_value=0, step=1)
        with c3: nu_ct = st.number_input("Nữ (L)", min_value=0, step=1)
        
        # Phần 2: Nghiệp vụ phiếu
        st.markdown("#### 📝 2. Nghiệp vụ Quản lý Phiếu")
        c4, c5, c6, c7 = st.columns(4)
        with c4: p_phat = st.number_input("Phát ra (M)", min_value=0, step=1)
        with c5: p_thu = st.number_input("Thu vào (N)", min_value=0, step=1)
        with c6: p_hop = st.number_input("Hợp lệ (O)", min_value=0, step=1)
        with c7: p_khong = st.number_input("K.Hợp lệ (P)", min_value=0, step=1)
        
        # Phần 3: Đại biểu (Lấy danh sách theo Đơn vị)
        st.markdown(f"#### 🏆 3. Kết quả Kiểm phiếu Đại biểu")
        don_vi = PHAN_BO_TO[st.session_state['ten_to']]
        kq_db = {}
        for db in DAN_SACH_DAI_BIEU[don_vi]:
            kq_db[db] = st.number_input(f"Số phiếu của: {db}", min_value=0, step=1)
            
        if st.form_submit_button("LƯU & GỬI BÁO CÁO", type="primary"):
            # Kiểm tra logic trước khi gửi
            if t_ct != (n_ct + nu_ct):
                st.error("❌ Lỗi: Tổng cử tri ≠ Nam + Nữ")
            elif p_thu != (p_hop + p_khong):
                st.error("❌ Lỗi: Phiếu thu vào ≠ Hợp lệ + Không hợp lệ")
            else:
                with st.spinner("Đang ghi vào Google Sheets..."):
                    h = st.session_state['hang_cua_to']
                    updates = []
                    # Ghi J-L
                    updates.append({'range': f'J{h}:L{h}', 'values': [[t_ct, n_ct, nu_ct]]})
                    # Ghi M-P
                    updates.append({'range': f'M{h}:P{h}', 'values': [[p_phat, p_thu, p_hop, p_khong]]})
                    # Ghi Đại biểu (Trỏ đích danh cột AA, AB...)
                    for name, val in kq_db.items():
                        col_letter = MAP_COT.get(name)
                        if col_letter:
                            updates.append({'range': f'{col_letter}{h}', 'values': [[val]]})
                    
                    try:
                        file_du_lieu.worksheet("Quoc Hoi").batch_update(updates)
                        st.success(f"✅ Đã lưu thành công vào Hàng {h}!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Lỗi gửi dữ liệu: {e}")

    if st.button("🔒 Đăng xuất"):
        st.session_state.update({'logged_in': False})
        st.rerun()
