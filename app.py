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

    # ==========================================
    # CẤU HÌNH DANH SÁCH & TỌA ĐỘ ĐẠI BIỂU
    # ==========================================
    # 1. Danh sách đại biểu theo Đơn vị bầu cử
    DANH_SACH_DAI_BIEU = {
        "Đơn vị số 1": ["Bà Nguyễn Thị Mai Dinh", "Bà Trần Thị B", "Ông Lê Văn C", "Bà Phạm Thị D", "Ông Đinh Văn E"],
        "Đơn vị số 2": ["Ông Vũ Văn F", "Bà Hoàng Thị G", "Ông Đặng Văn H", "Bà Lý Thị I"],
		"Đơn vị số 3": ["Ông Vũ Văn F", "Bà Hoàng Thị G", "Ông Đặng Văn H", "Bà Lý Thị I"],
        "Đơn vị số 4": ["Ông Trần Văn K", "Bà Lê Thị L", "Ông Phạm Văn M", "Bà Nguyễn Thị N"]
    }

    # 2. Bản đồ phân bổ Tổ (Điền đủ 46 tổ vào đây)
    PHAN_BO_TO = {
        "Tổ 1": "Đơn vị số 1", "Tổ 2": "Đơn vị số 1", "Tổ 3": "Đơn vị số 1",
        "Tổ 4": "Đơn vị số 2", "Tổ 5": "Đơn vị số 2", "Tổ 6": "Đơn vị số 2",
        "Tổ 7": "Đơn vị số 3", "Tổ 8": "Đơn vị số 3", "Tổ 9": "Đơn vị số 3"
    }

    # 3. Bản đồ trỏ CỘT trên Google Sheets cho từng Đại biểu (Bạn sửa các chữ M, N, O... cho khớp với file của bạn)
    TOA_DO_DAI_BIEU = {
        "Bà Nguyễn Mai Dinh": "AA", "Bà Trần Thị B": "N", "Ông Lê Văn C": "O", "Bà Phạm Thị D": "P", "Ông Đinh Văn E": "Q",
        "Ông Vũ Văn F": "R", "Bà Hoàng Thị G": "S", "Ông Đặng Văn H": "T", "Bà Lý Thị I": "U",
        "Ông Trần Văn K": "V", "Bà Lê Thị L": "W", "Ông Phạm Văn M": "X", "Bà Nguyễn Thị N": "Y"
    }

    # Nhận diện Tổ thuộc Đơn vị nào
    don_vi_cua_to = PHAN_BO_TO.get(st.session_state['ten_to'], "Chưa phân bổ")

    if don_vi_cua_to == "Chưa phân bổ":
        st.error(f"⚠️ {st.session_state['ten_to']} chưa được gắn vào Đơn vị bầu cử. Vui lòng kiểm tra lại cấu hình!")
        if st.button("🔒 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.stop()

    # ==========================================
    # GIAO DIỆN FORM NHẬP LIỆU
    # ==========================================
    cap_bau_cu = "Quoc Hoi" 
    try:
        sheet_target = file_du_lieu.worksheet(cap_bau_cu)
    except:
        st.error("Không tìm thấy dữ liệu cấp Quốc Hội.")
        st.stop()

    with st.form("Data_Entry_Form"):
        st.markdown("#### 1. Báo cáo tiến độ cử tri")
        col1, col2, col3 = st.columns(3)
        with col1:
            tong_cu_tri = st.number_input("Tổng số (J)", min_value=0, step=1)
        with col2:
            cu_tri_nam = st.number_input("Nam (K)", min_value=0, step=1)
        with col3:
            cu_tri_nu = st.number_input("Nữ (L)", min_value=0, step=1)
        
        st.divider()

        st.markdown(f"#### 2. Kết quả kiểm phiếu ({don_vi_cua_to})")
        
        danh_sach_ung_cu_vien = DANH_SACH_DAI_BIEU[don_vi_cua_to]
        ket_qua_phieu = {} # Từ điển lưu kết quả để chuẩn bị trỏ cột
        
        # Tự động sinh ô nhập liệu tương ứng với đại biểu
        for dai_bieu in danh_sach_ung_cu_vien:
            ket_qua_phieu[dai_bieu] = st.number_input(f"Số phiếu của: {dai_bieu}", min_value=0, step=1)
        
        st.write("")
        submit_data = st.form_submit_button("Lưu & Gửi báo cáo toàn bộ", type="primary")

        if submit_data:
            if tong_cu_tri != (cu_tri_nam + cu_tri_nu):
                st.error("⚠️ Lỗi logic: Tổng số cử tri không khớp với phép tính (Nam + Nữ).")
            elif tong_cu_tri == 0:
                st.warning("⚠️ Số liệu tổng cử tri đang bằng 0, vui lòng kiểm tra lại.")
            else:
                with st.spinner("Đang truyền dữ liệu về máy chủ phường..."):
                    hang_hien_tai = st.session_state['hang_cua_to']
                    
                    # TẠO GÓI DỮ LIỆU ĐỂ BẮN 1 LẦN DUY NHẤT LÊN GOOGLE SHEETS (Batch Update)
                    goi_du_lieu = []
                    
                    # 1. Gói số liệu Cử tri (Trỏ vào J, K, L)
                    goi_du_lieu.append({
                        'range': f'J{hang_hien_tai}:L{hang_hien_tai}',
                        'values': [[tong_cu_tri, cu_tri_nam, cu_tri_nu]]
                    })
                    
                    # 2. Gói số liệu Phiếu đại biểu (Trỏ vào các cột tương ứng đã cấu hình)
                    for dai_bieu, phieu in ket_qua_phieu.items():
                        cot_tuong_ung = TOA_DO_DAI_BIEU.get(dai_bieu)
                        if cot_tuong_ung:
                            goi_du_lieu.append({
                                'range': f'{cot_tuong_ung}{hang_hien_tai}',
                                'values': [[phieu]]
                            })
                    
                    try:
                        # Thực thi lệnh bắn gói dữ liệu
                        sheet_target.batch_update(goi_du_lieu)
                        time.sleep(0.5) 
                        st.success(f"✅ Đã lưu thành công dữ liệu Cử tri và Số phiếu Đại biểu!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Lỗi đường truyền, vui lòng thử lại: {e}")

    if st.button("🔒 Đăng xuất an toàn"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    st.markdown("<div style='text-align: center; color: grey; font-size: 12px; margin-top: 30px;'>© 2026 - Bản quyền thuộc UBND Phường Tân Phong</div>", unsafe_allow_html=True)

