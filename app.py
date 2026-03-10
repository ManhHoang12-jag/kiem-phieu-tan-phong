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
# 6. KHU VỰC NHẬP LIỆU CHÍNH THỨC
# ==========================================
else:
    st.info(f"👤 Đang thao tác: **{st.session_state['ten_to']}** | 📍 Vị trí lưu trữ: **Hàng {st.session_state['hang_cua_to']}**")

    cap_bau_cu = "Quoc Hoi" 
    try:
        sheet_target = file_du_lieu.worksheet(cap_bau_cu)
    except:
        st.error("Không tìm thấy dữ liệu cấp Quốc Hội.")
        st.stop()

    with st.form("Data_Entry_Form"):
        st.markdown("#### Báo cáo số lượng cử tri đi bầu")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            tong_cu_tri = st.number_input("Tổng số (J)", min_value=0, step=1)
        with col2:
            cu_tri_nam = st.number_input("Nam (K)", min_value=0, step=1)
        with col3:
            cu_tri_nu = st.number_input("Nữ (L)", min_value=0, step=1)
        
        st.write("")
        submit_data = st.form_submit_button("Lưu & Gửi báo cáo", type="primary")

        if submit_data:
            if tong_cu_tri != (cu_tri_nam + cu_tri_nu):
                st.error("⚠️ Lỗi logic: Tổng số cử tri không khớp với phép tính (Nam + Nữ).")
            elif tong_cu_tri == 0:
                st.warning("⚠️ Số liệu đang bằng 0, vui lòng nhập số liệu trước khi gửi.")
            else:
                with st.spinner("Đang truyền dữ liệu về máy chủ..."):
                    du_lieu_cu_tri = [[tong_cu_tri, cu_tri_nam, cu_tri_nu]]
                    hang_hien_tai = st.session_state['hang_cua_to']
                    vung_cap_nhat = f"J{hang_hien_tai}:L{hang_hien_tai}"
                    
                    try:
                        sheet_target.update(vung_cap_nhat, du_lieu_cu_tri)
                        time.sleep(0.5) 
                        st.success(f"✅ Đã lưu thành công lên hệ thống tổng!")
                        st.balloons()
                    except Exception as e:
                        st.error("❌ Lỗi đường truyền, vui lòng thử lại sau 1 phút.")

    if st.button("🔒 Đăng xuất an toàn"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    st.markdown("<div style='text-align: center; color: grey; font-size: 12px; margin-top: 30px;'>© 2026 - Bản quyền thuộc UBND Phường Tân Phong</div>", unsafe_allow_html=True)
