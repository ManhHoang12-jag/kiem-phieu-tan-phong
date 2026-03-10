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
# ==========================================
# 6. PHẦN NHẬP LIỆU ĐA CẤP (QUỐC HỘI, HĐND TỈNH, HĐND PHƯỜNG)
# ==========================================
else:
    st.info(f"👤 Tổ đang thao tác: **{st.session_state['ten_to']}** | 📍 Hàng lưu trữ: **{st.session_state['hang_cua_to']}**")

    # --- 1. CẤU HÌNH ĐẠI BIỂU THEO CẤP ---
    # Bạn thay tên đại biểu thực tế vào đây
    DANH_SACH_DAI_BIEU = {
        "Quốc hội": ["Đại biểu Quốc Hội A", "Đại biểu Quốc Hội B"],
        "HĐND tỉnh": ["Đại biểu Tỉnh C", "Đại biểu Tỉnh D"],
        "HĐND phường": ["Đại biểu Phường E", "Đại biểu Phường F"]
    }

    # --- 2. TRỎ CỘT ĐÍCH DANH (CHÚ Ý CỘT AA TẠI ĐÂY) ---
    # Tên ở đây phải khớp 100% với tên ở danh sách trên
    MAP_COT_DAI_BIEU = {
        "Đại biểu Quốc Hội A": "AA",
        "Đại biểu Quốc Hội B": "AB",
        "Đại biểu Tỉnh C": "AA",  # Sang sheet HĐND tỉnh, người này lại nhập từ cột AA
        "Đại biểu Tỉnh D": "AB",
        "Đại biểu Phường E": "AA",
        "Đại biểu Phường F": "AB"
    }

    # --- 3. BẢN ĐỒ CHUYỂN HƯỚNG TÊN TAB TRÊN GOOGLE SHEETS ---
    MAP_SHEET = {
        "Quốc hội": "Quoc Hoi",
        "HĐND tỉnh": "HDND Tinh",
        "HĐND phường": "HDND Phuong"
    }

    with st.form("Form_Nhap_Lieu"):
        st.markdown("#### 📌 BƯỚC 1: CHỌN CẤP BẦU CỬ")
        # Thanh trỏ xuống chọn cấp bầu cử
        cap_bau_cu = st.selectbox("Chọn cấp báo cáo:", ["Quốc hội", "HĐND tỉnh", "HĐND phường"])
        
        st.divider()
        
        st.markdown("#### 📊 BƯỚC 2: TIẾN ĐỘ CỬ TRI")
        c1, c2, c3 = st.columns(3)
        with c1: t_ct = st.number_input("Tổng cử tri (J)", min_value=0, step=1)
        with c2: n_ct = st.number_input("Nam (K)", min_value=0, step=1)
        with c3: nu_ct = st.number_input("Nữ (L)", min_value=0, step=1)
        
        st.markdown("#### 📝 BƯỚC 3: QUẢN LÝ PHIẾU")
        c4, c5, c6, c7 = st.columns(4)
        with c4: p_phat = st.number_input("Phát ra (M)", min_value=0, step=1)
        with c5: p_thu = st.number_input("Thu vào (N)", min_value=0, step=1)
        with c6: p_hop = st.number_input("Hợp lệ (O)", min_value=0, step=1)
        with c7: p_khong = st.number_input("K.Hợp lệ (P)", min_value=0, step=1)
        
        # Tiêu đề sẽ tự động đổi theo cấp đang chọn
        st.markdown(f"#### 🏆 BƯỚC 4: KẾT QUẢ KIỂM PHIẾU ({cap_bau_cu.upper()})")
        
        # Tự động lấy danh sách người ứng cử của cấp đó
        danh_sach_hien_tai = DANH_SACH_DAI_BIEU[cap_bau_cu]
        kq_db = {}
        for db in danh_sach_hien_tai:
            kq_db[db] = st.number_input(f"Số phiếu của: {db}", min_value=0, step=1)
            
        if st.form_submit_button("LƯU & GỬI BÁO CÁO", type="primary"):
            # Kiểm tra toán học trước khi cho gửi
            if t_ct != (n_ct + nu_ct):
                st.error("❌ Lỗi: Tổng cử tri không khớp phép tính (Nam + Nữ)!")
            elif p_thu != (p_hop + p_khong):
                st.error("❌ Lỗi: Phiếu thu vào không khớp (Hợp lệ + Không hợp lệ)!")
            else:
                # Tìm đúng tên tab Google Sheets để bắn dữ liệu
                sheet_name = MAP_SHEET[cap_bau_cu]
                
                with st.spinner(f"Đang ghi dữ liệu vào Sheet '{sheet_name}'..."):
                    h = st.session_state['hang_cua_to']
                    updates = []
                    
                    updates.append({'range': f'J{h}:L{h}', 'values': [[t_ct, n_ct, nu_ct]]})
                    updates.append({'range': f'M{h}:P{h}', 'values': [[p_phat, p_thu, p_hop, p_khong]]})
                    
                    # Bắn số phiếu đại biểu vào cột AA, AB...
                    for name, val in kq_db.items():
                        col_letter = MAP_COT_DAI_BIEU.get(name)
                        if col_letter:
                            updates.append({'range': f'{col_letter}{h}', 'values': [[val]]})
                    
                    try:
                        # Kết nối và cập nhật đúng tab
                        sheet_target = file_du_lieu.worksheet(sheet_name)
                        sheet_target.batch_update(updates)
                        st.success(f"✅ Đã lưu báo cáo cấp {cap_bau_cu} thành công!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Lỗi: Không tìm thấy tab '{sheet_name}' trên file Google Sheets. Hãy tạo tab mới có tên y hệt như vậy ở dưới cùng file Excel.")

    if st.button("🔒 Đăng xuất"):
        st.session_state.update({'logged_in': False})
        st.rerun()
        
    st.markdown("<div style='text-align: center; color: grey; font-size: 12px; margin-top: 30px;'>© 2026 - Bản quyền thuộc UBND Phường Tân Phong</div>", unsafe_allow_html=True)



