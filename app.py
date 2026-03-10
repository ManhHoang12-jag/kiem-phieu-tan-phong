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
# ==========================================
# 6. PHẦN NHẬP LIỆU ĐA CẤP (LOGIC CHUẨN NGHIỆP VỤ)
# ==========================================
else:
    st.info(f"👤 Tổ đang thao tác: **{st.session_state['ten_to']}** | 📍 Hàng lưu trữ: **{st.session_state['hang_cua_to']}**")

    # --- 1. PHÂN BỔ 47 TỔ VÀO 7 ĐƠN VỊ (CẤP PHƯỜNG) ---
    # Bạn hãy tự chỉnh lại các con số này cho khớp với Quyết định phê duyệt của phường nhé:
    PHAN_BO_PHUONG = {}
    for i in range(1, 48):
        if i <= 7: PHAN_BO_PHUONG[f"Tổ {i}"] = "Đơn vị 1"
        elif i <= 14: PHAN_BO_PHUONG[f"Tổ {i}"] = "Đơn vị 2"
        elif i <= 21: PHAN_BO_PHUONG[f"Tổ {i}"] = "Đơn vị 3"
        elif i <= 28: PHAN_BO_PHUONG[f"Tổ {i}"] = "Đơn vị 4"
        elif i <= 35: PHAN_BO_PHUONG[f"Tổ {i}"] = "Đơn vị 5"
        elif i <= 42: PHAN_BO_PHUONG[f"Tổ {i}"] = "Đơn vị 6"
        else: PHAN_BO_PHUONG[f"Tổ {i}"] = "Đơn vị 7"
    
    don_vi_phuong_cua_to = PHAN_BO_PHUONG.get(st.session_state['ten_to'], "Đơn vị 1")

    # --- 2. CẤU HÌNH DANH SÁCH ĐẠI BIỂU ---
    # Cấp Quốc hội & Tỉnh (Cố định cho mọi Tổ)
    DS_QUOC_HOI = ["Đoàn Thị C", "Đại biểu QH 2", "Đại biểu QH 3", "Trần Văn Bê", "Hà Thị G"]
    DS_TINH = ["Đại biểu Tỉnh 1", "Đại biểu Tỉnh 2", "Đại biểu Tỉnh 3", "Đại Biểu Tỉnh 5"]
    
    # Cấp Phường (Thay đổi theo 7 Đơn vị)
    DS_PHUONG = {
        "Đơn vị 1": ["Đại biểu P1_A", "Đại biểu P1_B", "Đại biểu P1_C", "Nguyễn Trung C", "Đàm Đức Hiếu"],
        "Đơn vị 2": ["Đại biểu P2_A", "Đại biểu P2_B"],
        "Đơn vị 3": ["Đại biểu P3_A", "Đại biểu P3_B", "Đại biểu P3_C"],
        "Đơn vị 4": ["Đại biểu P4_A", "Đại biểu P4_B"],
        "Đơn vị 5": ["Đại biểu P5_A", "Đại biểu P5_B"],
        "Đơn vị 6": ["Đại biểu P6_A", "Đại biểu P6_B"],
        "Đơn vị 7": ["Đại biểu P7_A", "Đại biểu P7_B", "Đại biểu P7_C"]
    }

    # --- 3. BẢN ĐỒ TRỎ CỘT ĐÍCH DANH TRÊN GOOGLE SHEETS ---
    MAP_COT_DAI_BIEU = {
        "Đoàn Thị C": "AA", "Đại biểu QH 2": "AB", "Đại biểu QH 3": "AC",
        "Đại biểu Tỉnh 1": "AA", "Đại biểu Tỉnh 2": "AB", "Đại biểu Tỉnh 3": "AC",
        
        # Lưu ý: Các đại biểu phường dù khác tên nhưng vẫn trỏ chung vào AA, AB, AC... 
        # vì dữ liệu của họ sẽ chạy vào các hàng khác nhau trên Sheet HĐND Phường
        "Đại biểu P1_A": "AA", "Đại biểu P1_B": "AB", "Đại biểu P1_C": "AC",
        "Đại biểu P2_A": "AA", "Đại biểu P2_B": "AB",
        "Đại biểu P3_A": "AA", "Đại biểu P3_B": "AB", "Đại biểu P3_C": "AC",
        "Đại biểu P4_A": "AA", "Đại biểu P4_B": "AB",
        "Đại biểu P5_A": "AA", "Đại biểu P5_B": "AB",
        "Đại biểu P6_A": "AA", "Đại biểu P6_B": "AB",
        "Đại biểu P7_A": "AA", "Đại biểu P7_B": "AB", "Đại biểu P7_C": "AC"
    }

    MAP_SHEET = {
        "Quốc hội": "Quoc Hoi",
        "HĐND tỉnh": "HDND Tinh",
        "HĐND phường": "HDND Phuong"
    }

    # --- CHỌN CẤP BẦU CỬ (ĐẶT NGOÀI FORM) ---
    st.markdown("#### 📌 BƯỚC 1: CHỌN CẤP BẦU CỬ")
    cap_bau_cu = st.selectbox("Chọn cấp để báo cáo:", ["Quốc hội", "HĐND tỉnh", "HĐND phường"])
    
    # Logic xác định danh sách đại biểu
    if cap_bau_cu == "Quốc hội":
        danh_sach_hien_tai = DS_QUOC_HOI
        thong_bao = "Toàn phường"
    elif cap_bau_cu == "HĐND tỉnh":
        danh_sach_hien_tai = DS_TINH
        thong_bao = "Toàn phường"
    else:
        danh_sach_hien_tai = DS_PHUONG[don_vi_phuong_cua_to]
        thong_bao = f"Khu vực: {don_vi_phuong_cua_to}"
        
    st.info(f"🔎 Bạn đang nhập liệu cho: **{cap_bau_cu}** ({thong_bao})")
    st.divider()

    # --- FORM NHẬP LIỆU ---
    with st.form("Form_Nhap_Lieu"):
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
        
        st.markdown(f"#### 🏆 BƯỚC 4: KẾT QUẢ KIỂM PHIẾU")
        kq_db = {}
        for db in danh_sach_hien_tai:
            kq_db[db] = st.number_input(f"Số phiếu của: {db}", min_value=0, step=1)
            
        if st.form_submit_button("LƯU & GỬI BÁO CÁO", type="primary"):
            if t_ct != (n_ct + nu_ct) or p_thu != (p_hop + p_khong):
                st.error("❌ Lỗi logic toán học (Cử tri hoặc Số phiếu không khớp)!")
            else:
                sheet_name = MAP_SHEET[cap_bau_cu]
                with st.spinner(f"Đang ghi dữ liệu vào Sheet '{sheet_name}'..."):
                    h = st.session_state['hang_cua_to']
                    updates = []
                    
                    updates.append({'range': f'J{h}:L{h}', 'values': [[t_ct, n_ct, nu_ct]]})
                    updates.append({'range': f'M{h}:P{h}', 'values': [[p_phat, p_thu, p_hop, p_khong]]})
                    
                    for name, val in kq_db.items():
                        col_letter = MAP_COT_DAI_BIEU.get(name)
                        if col_letter:
                            updates.append({'range': f'{col_letter}{h}', 'values': [[val]]})
                    
                    try:
                        file_du_lieu.worksheet(sheet_name).batch_update(updates)
                        st.success(f"✅ Đã lưu báo cáo cấp {cap_bau_cu} thành công!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Lỗi: Không tìm thấy tab '{sheet_name}' trên file Google Sheets.")

    if st.button("🔒 Đăng xuất"):
        st.session_state.update({'logged_in': False})
        st.rerun()
        
    st.markdown("<div style='text-align: center; color: grey; font-size: 12px; margin-top: 30px;'>© 2026 - Bản quyền thuộc UBND Phường Tân Phong</div>", unsafe_allow_html=True)






