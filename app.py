import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import time
import base64
import os

# ==========================================
# 1. THIẾT LẬP GIAO DIỆN CHÍNH THỨC
# ==========================================
st.set_page_config(page_title="Hệ thống Báo cáo Bầu cử phường Tân Phong", page_icon="🇻🇳", layout="centered")

css_sach_se = """
<style>
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    header {visibility: hidden !important; display: none !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
    .viewerBadge_container__1QSob, .viewerBadge_link__1S137 {display: none !important;}
    .block-container {padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 800px;}
    .stButton>button {width: 100%; font-weight: bold; border-radius: 8px;}
</style>
"""
st.markdown(css_sach_se, unsafe_allow_html=True)

# ==========================================
# 2. CẤU HÌNH KẾT NỐI GOOGLE SHEETS
# ==========================================
@st.cache_resource(show_spinner=False)
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Solieubaucutanphong")

try:
    file_du_lieu = init_connection()
except Exception as e:
    st.error(f"Lỗi kết nối máy chủ: {e}")
    st.stop()

# ==========================================
# 3. TRẠNG THÁI & HÀNG MỎ NEO
# ==========================================
HANG_MO_NEO = 6 

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'ten_to': '', 'hang_cua_to': 0})

# ==========================================
# 4. HEADER QUỐC HUY (CÔNG NGHỆ BASE64 VƯỢT TƯỜNG LỬA)
# ==========================================
# Hệ thống sẽ tìm file logo.png bạn đã tải lên GitHub và biến nó thành mã nội bộ
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        encoded_img = base64.b64encode(f.read()).decode()
    img_src = f"data:image/png;base64,{encoded_img}"
else:
    # Nếu bạn quên chưa tải logo.png, nó sẽ dùng hình Cờ Việt Nam tạm thời
    img_src = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Flag_of_Vietnam.svg/200px-Flag_of_Vietnam.svg.png"

header_html = f"""<div style="display: flex; align-items: center; border-bottom: 2px solid #cc0000; padding-bottom: 15px; margin-bottom: 25px;"><img src="{img_src}" width="75" style="margin-right: 15px; flex-shrink: 0;"><div style="flex-grow: 1; overflow: hidden;"><h3 style="margin: 0; color: #cc0000; font-size: clamp(14px, 4vw, 20px); white-space: nowrap;">ỦY BAN NHÂN DÂN PHƯỜNG TÂN PHONG</h3><h5 style="margin: 0; color: #333333; font-size: clamp(12px, 3.5vw, 16px); margin-top: 4px; white-space: nowrap;">Cổng Nhập liệu Bầu cử Trực tuyến</h5></div></div>"""

st.markdown(header_html, unsafe_allow_html=True)

# ==========================================
# 5. KHU VỰC ĐĂNG NHẬP
# ==========================================
if not st.session_state['logged_in']:
    st.markdown("#### Xác thực cán bộ Tổ bầu cử")
    with st.form("Login_Form"):
        danh_sach_to = [f"Tổ {i}" for i in range(1, 47)]
        user_choice = st.selectbox("Chọn đơn vị công tác:", danh_sach_to)
        password_input = st.text_input("Mã bảo mật:", type="password")
        
        submit_login = st.form_submit_button("Đăng nhập hệ thống", type="primary")

        if submit_login:
            so_thu_tu_to = int(user_choice.replace("Tổ ", ""))
            hang_thuc_te = HANG_MO_NEO + (so_thu_tu_to - 1)
            
            try:
                sheet_check = file_du_lieu.worksheet("Quoc Hoi")
                mat_khau_he_thong = sheet_check.cell(hang_thuc_te, 2).value 
                
                if str(password_input) == str(mat_khau_he_thong):
                    st.session_state['logged_in'] = True
                    st.session_state['ten_to'] = user_choice
                    st.session_state['hang_cua_to'] = hang_thuc_te
                    st.rerun()
                else:
                    st.error("❌ Mã bảo mật không chính xác!")
            except Exception as e:
                st.error(f"Lỗi truy xuất hệ thống: {e}")

# ==========================================
# 6. KHU VỰC NHẬP LIỆU CHÍNH THỨC (BỔ SUNG QUẢN LÝ PHIẾU)
# ==========================================
else:
    st.info(f"👤 **{st.session_state['ten_to']}** | 📍 Hàng dữ liệu: **{st.session_state['hang_cua_to']}**")

    # --- CẤU HÌNH DANH SÁCH ĐẠI BIỂU ---
    DANH_SACH_DAI_BIEU = {
        "Đơn vị số 1": ["Vừ Thị Mai Dinh", "Đại biểu B", "Đại biểu C"],
        "Đơn vị số 2": ["Đại biểu D", "Đại biểu E", "Đại biểu F"]
    }

    # --- CẤU HÌNH TRỎ CỘT (QUAN TRỌNG: Bạn sửa các chữ cái này cho khớp với file Sheets của bạn) ---
    MAP_COT = {
        # Phần quản lý phiếu chung
        "phieu_phat_ra": "S",
        "phieu_thu_vao": "U",
        "phieu_hop_le": "W",
        "phieu_khong_hop_le": "P",
        # Phần đại biểu (Ví dụ trỏ tiếp từ cột Q trở đi)
        "Vừa Thị Mai Dinh": "AA", "Đại biểu B": "R", "Đại biểu C": "S",
        "Đại biểu D": "T", "Đại biểu E": "U", "Đại biểu F": "V"
    }

    PHAN_BO_TO = {f"Tổ {i}": "Đơn vị số 1" if i <= 23 else "Đơn vị số 2" for i in range(1, 47)}
    don_vi_cua_to = PHAN_BO_TO.get(st.session_state['ten_to'], "Đơn vị số 1")

    with st.form("Full_Data_Form"):
        st.markdown("#### 1. Tiến độ cử tri (Cập nhật liên tục)")
        c1, c2, c3 = st.columns(3)
        with c1: tong = st.number_input("Tổng số cử tri (J)", min_value=0, step=1)
        with c2: nam = st.number_input("Nam (K)", min_value=0, step=1)
        with c3: nu = st.number_input("Nữ (L)", min_value=0, step=1)

        st.divider()
        st.markdown("#### 2. Nghiệp vụ Quản lý Phiếu (Sau khi kiểm phiếu)")
        c4, c5 = st.columns(2)
        with c4: p_phat = st.number_input("Số phiếu phát ra (M)", min_value=0, step=1)
        with c5: p_thu = st.number_input("Số phiếu thu vào (N)", min_value=0, step=1)
        
        c6, c7 = st.columns(2)
        with c6: p_hople = st.number_input("Số phiếu hợp lệ (O)", min_value=0, step=1)
        with c7: p_khonghople = st.number_input("Số phiếu không hợp lệ (P)", min_value=0, step=1)

        st.divider()
        st.markdown(f"#### 3. Kết quả bầu cử Đại biểu ({don_vi_cua_to})")
        kq_dai_bieu = {}
        for db in DANH_SACH_DAI_BIEU[don_vi_cua_to]:
            kq_dai_bieu[db] = st.number_input(f"Số phiếu của: {db}", min_value=0, step=1)

        if st.form_submit_button("Lưu & Gửi báo cáo toàn bộ", type="primary"):
            # Kiểm tra logic phiếu
            if p_thu != (p_hople + p_khonghople):
                st.error("❌ Lỗi: Phiếu thu vào phải bằng Hợp lệ + Không hợp lệ!")
            elif tong != (nam + nu):
                st.error("❌ Lỗi: Tổng cử tri không khớp Nam + Nữ!")
            else:
                with st.spinner("Đang truyền dữ liệu..."):
                    hang = st.session_state['hang_cua_to']
                    updates = []
                    
                    # Gom dữ liệu cử tri (J-L)
                    updates.append({'range': f'J{hang}:L{hang}', 'values': [[tong, nam, nu]]})
                    # Gom dữ liệu phiếu (M-P)
                    updates.append({'range': f'{MAP_COT["phieu_phat_ra"]}{hang}:{MAP_COT["phieu_khong_hop_le"]}{hang}', 
                                    'values': [[p_phat, p_thu, p_hople, p_khonghople]]})
                    # Gom dữ liệu từng đại biểu
                    for db_name, so_phieu in kq_dai_bieu.items():
                        col = MAP_COT.get(db_name)
                        if col: updates.append({'range': f'{col}{hang}', 'values': [[so_phieu]]})
                    
                    try:
                        file_du_lieu.worksheet("Quoc Hoi").batch_update(updates)
                        st.success("✅ Đã lưu báo cáo thành công!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

    if st.button("🔒 Đăng xuất"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    st.markdown("<div style='text-align: center; color: grey; font-size: 12px; margin-top: 30px;'>© 2026 - Bản quyền thuộc UBND Phường Tân Phong</div>", unsafe_allow_html=True)


