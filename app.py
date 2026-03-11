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
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as f:
        encoded_img = base64.b64encode(f.read()).decode()
    img_src = f"data:image/png;base64,{encoded_img}"
else:
    img_src = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Flag_of_Vietnam.svg/200px-Flag_of_Vietnam.svg.png"

header_html = f"""<div style="display: flex; align-items: center; border-bottom: 2px solid #cc0000; padding-bottom: 15px; margin-bottom: 25px;"><img src="{img_src}" width="75" style="margin-right: 15px; flex-shrink: 0;"><div style="flex-grow: 1; overflow: hidden;"><h3 style="margin: 0; color: #cc0000; font-size: clamp(14px, 4vw, 20px); white-space: nowrap;">ỦY BAN NHÂN DÂN PHƯỜNG TÂN PHONG</h3><h5 style="margin: 0; color: #333333; font-size: clamp(12px, 3.5vw, 16px); margin-top: 4px; white-space: nowrap;">Cổng Nhập liệu Bầu cử Trực tuyến</h5></div></div>"""

st.markdown(header_html, unsafe_allow_html=True)

# ==========================================
# 5. KHU VỰC ĐĂNG NHẬP
# ==========================================
if not st.session_state['logged_in']:
    st.markdown("#### Xác thực cán bộ Tổ bầu cử")
    with st.form("Login_Form"):
        danh_sach_to = [f"Tổ {i}" for i in range(1, 48)]
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
# 6. PHẦN NHẬP LIỆU ĐA CẤP (PHÂN BỔ THỦ CÔNG & TỌA ĐỘ ĐA CẤP)
# ==========================================
else:
    st.info(f"👤 Tổ đang thao tác: **{st.session_state['ten_to']}**")

    # --- 1. PHÂN BỔ 47 TỔ VÀO 7 ĐƠN VỊ CẤP PHƯỜNG ---
    PHAN_BO_PHUONG = {
        "Tổ 1": "Đơn vị 1", "Tổ 2": "Đơn vị 1", "Tổ 3": "Đơn vị 1", "Tổ 4": "Đơn vị 1", "Tổ 5": "Đơn vị 1", "Tổ 6": "Đơn vị 1", "Tổ 7": "Đơn vị 2", 
        "Tổ 8": "Đơn vị 2", "Tổ 9": "Đơn vị 2", "Tổ 10": "Đơn vị 2", "Tổ 11": "Đơn vị 2", "Tổ 12": "Đơn vị 2", "Tổ 13": "Đơn vị 3", "Tổ 14": "Đơn vị 3",
        "Tổ 15": "Đơn vị 3", "Tổ 16": "Đơn vị 3", "Tổ 17": "Đơn vị 3", "Tổ 18": "Đơn vị 4", "Tổ 19": "Đơn vị 4", "Tổ 20": "Đơn vị 4", "Tổ 21": "Đơn vị 4",
        "Tổ 22": "Đơn vị 4", "Tổ 23": "Đơn vị 4", "Tổ 24": "Đơn vị 4", "Tổ 25": "Đơn vị 5", "Tổ 26": "Đơn vị 5", "Tổ 27": "Đơn vị 5", "Tổ 28": "Đơn vị 5",
        "Tổ 29": "Đơn vị 5", "Tổ 30": "Đơn vị 5", "Tổ 31": "Đơn vị 5", "Tổ 32": "Đơn vị 5", "Tổ 33": "Đơn vị 5", "Tổ 34": "Đơn vị 6", "Tổ 35": "Đơn vị 6",
        "Tổ 36": "Đơn vị 6", "Tổ 37": "Đơn vị 6", "Tổ 38": "Đơn vị 6", "Tổ 39": "Đơn vị 6", "Tổ 40": "Đơn vị 6", "Tổ 41": "Đơn vị 7", "Tổ 42": "Đơn vị 7",
        "Tổ 43": "Đơn vị 7", "Tổ 44": "Đơn vị 7", "Tổ 45": "Đơn vị 7", "Tổ 46": "Đơn vị 7", "Tổ 47": "Đơn vị 7"
    }
    don_vi_phuong_cua_to = PHAN_BO_PHUONG.get(st.session_state['ten_to'], "Chưa có đơn vị")

    # --- TÍNH NĂNG MỚI: BẢN ĐỒ DÒNG (ROW) DÀNH RIÊNG CHO CẤP PHƯỜNG ---
    MAP_HANG_PHUONG = {
        "Tổ 1": 7, "Tổ 2": 8, "Tổ 3": 9, "Tổ 4": 10, "Tổ 5": 11, "Tổ 6": 12,
        "Tổ 7": 15, "Tổ 8": 16, "Tổ 9": 17, "Tổ 10": 18, "Tổ 11": 19, "Tổ 12": 20,
        "Tổ 13": 23, "Tổ 14": 24, "Tổ 15": 25, "Tổ 16": 26, "Tổ 17": 27, "Tổ 18": 30, "Tổ 19": 31, "Tổ 20": 32, "Tổ 21": 33, "Tổ 22": 34, "Tổ 23": 35, "Tổ 24": 36,
        "Tổ 25": 39, "Tổ 26": 40, "Tổ 27": 41, "Tổ 28": 42, "Tổ 29": 43, "Tổ 30": 44, "Tổ 31": 45, "Tổ 32": 46, "Tổ 33": 47,
        "Tổ 34": 50, "Tổ 35": 51, "Tổ 36": 52, "Tổ 37": 53, "Tổ 38": 54, "Tổ 39": 55, "Tổ 40": 56,
        "Tổ 41": 59, "Tổ 42": 60, "Tổ 43": 61, "Tổ 44": 62, "Tổ 45": 63, "Tổ 46": 64, "Tổ 47": 65
    }

    # --- 2. CẤU HÌNH DANH SÁCH ĐẠI BIỂU ---
    DS_QUOC_HOI = ["Vừ Thị Mai Dinh", "Vũ Minh Đạo", "Sùng A Hồ", "Vì Thị Ngoan", "Cà Thị Thắm"]
    DS_TINH = ["Phạm Văn Đức", "Vương Văn Lợi", "Hầu Thị Mỉ", "Lê Minh Ngân", "Thùng Xuân Thành", "Trần Thị Phước Thủy", "Nguyễn Xuân Thức", "Mùa A Trừ"]
    DS_PHUONG = {
        "Đơn vị 1": ["Hoàng Tuấn Anh", "Trần Thị Cậy", "Nguyễn Thị Thanh Duyên", "Lê Quang Hòa", "Nguyễn Văn Nghiệp", "Đỗ Thị Nụ", "Bùi Thị Thảo"],
        "Đơn vị 2": ["Lỳ Gió Chứ", "Lê Ngọc Dũng", "Vàng Thị Lan", "Dương Thị Nhài", "Nguyễn Thị Thắm", "Đỗ Văn Thủy", "Nguyễn Thị Hải Yến"],
        "Đơn vị 3": ["Lê Hải Hùng", "Nguyễn Văn Long", "Lê Văn Phong", "Lê Hồng Quyết", "Đào Văn Trọng"],
        "Đơn vị 4": ["Nguyễn Thị Hòa", "Lèng Văn Pây", "Lù Văn Thắng", "Nguyễn Thị Thược", "Mùa A Trừ"],
        "Đơn vị 5": ["Vùi Văn Chài", "Lù Thị Kim Cương", "Lò Văn Sung", "Tống Thị Thanh Thắm", "Trần Văn Tìm"],
        "Đơn vị 6": ["Phạm Thị Hà", "Thào A Phử", "Lý A Tủa"],
        "Đơn vị 7": ["Lê Xuân Dũng", "Hảng A Nhà", "Thào A Phình", "Lèng Văn Sơn", "Vàng Văn Tem"],
    }

    # --- 3. BẢN ĐỒ TỌA ĐỘ CHI TIẾT ---
    MAP_TOA_DO_CHI_TIET = {
        "Quốc hội": {
            "tong_ct": "J", "nam": "K", "nu": "L",
            "phat": "S", "thu": "U", "hop": "W", "khong": "Y",
            "dai_bieu": {
                "Vừ Thị Mai Dinh": "AA", "Vũ Minh Đạo": "AC", "Sùng A Hồ": "AE", 
                "Vì Thị Ngoan": "AG", "Cà Thị Thắm": "AI"
            }
        },
        "HĐND tỉnh": {
            "tong_ct": "J", "nam": "K", "nu": "L",
            "phat": "S", "thu": "U", "hop": "W", "khong": "Y",
            "dai_bieu": {
                "Phạm Văn Đức": "AA", "Vương Văn Lợi": "AC", "Hầu Thị Mỉ": "AE", "Lê Minh Ngân": "AG", "Thùng Xuân Thành": "AI", "Trần Thị Phước Thủy": "AK", "Nguyễn Xuân Thức": "AM", "Mùa A Trừ": "AO"
            }
        },
        "HĐND phường": {
            "tong_ct": "I", "nam": "J", "nu": "K",  
            "phat": "R", "thu": "T", "hop": "V", "khong": "X",
            "dai_bieu": {
                "Hoàng Tuấn Anh": "Z", "Trần Thị Cậy": "AB", "Nguyễn Thị Thanh Duyên": "AD", "Lê Quang Hòa": "AF", "Nguyễn Văn Nghiệp": "AH", "Đỗ Thị Nụ": "AJ", "Bùi Thị Thảo": "AL",
                "Lỳ Gió Chứ": "Z", "Lê Ngọc Dũng": "AB", "Vàng Thị Lan": "AD", "Dương Thị Nhài": "AF", "Nguyễn Thị Thắm": "AH", "Đỗ Văn Thủy": "AJ", "Nguyễn Thị Hải Yến": "AL",
                "Lê Hải Hùng": "Z", "Nguyễn Văn Long": "AB", "Lê Văn Phong": "AD", "Lê Hồng Quyết": "AF", "Đào Văn Trọng": "AH",
                "Nguyễn Thị Hòa": "Z", "Lèng Văn Pây": "AB", "Lù Văn Thắng": "AD", "Nguyễn Thị Thược": "AF", "Mùa A Trừ": "AH",
                "Vùi Văn Chài": "Z", "Lù Thị Kim Cương": "AB", "Lò Văn Sung": "AD", "Tống Thị Thanh Thắm": "AF", "Trần Văn Tìm": "AH",
                "Phạm Thị Hà": "Z", "Thào A Phử": "AB", "Lý A Tủa": "AD",
                "Lê Xuân Dũng": "Z", "Hảng A Nhà": "AB", "Thào A Phình": "AD", "Lèng Văn Sơn": "AF", "Trần Văn Tìm": "AH"
            }
        }
    }

    MAP_SHEET = {
        "Quốc hội": "Quoc Hoi",
        "HĐND tỉnh": "HDND Tinh",
        "HĐND phường": "HDND Phuong"
    }

    # --- CHỌN CẤP BẦU CỬ ---
    st.markdown("#### BƯỚC 1: CHỌN CẤP BẦU CỬ")
    cap_bau_cu = st.selectbox("Chọn cấp để báo cáo:", ["Quốc hội", "HĐND tỉnh", "HĐND phường"])
    
    if cap_bau_cu == "Quốc hội":
        danh_sach_hien_tai = DS_QUOC_HOI
        thong_bao = "Toàn phường"
    elif cap_bau_cu == "HĐND tỉnh":
        danh_sach_hien_tai = DS_TINH
        thong_bao = "Toàn phường"
    else:
        if don_vi_phuong_cua_to == "Chưa có đơn vị":
            st.error("⚠️ Lỗi: Hệ thống chưa được cấu hình Đơn vị bầu cử cho Tổ này. Vui lòng liên hệ quản trị viên!")
            st.stop()
            
        danh_sach_hien_tai = DS_PHUONG[don_vi_phuong_cua_to]
        thong_bao = f"Khu vực: {don_vi_phuong_cua_to}"
        
    st.info(f"🔎 Đang nhập liệu cho: **{cap_bau_cu}** ({thong_bao})")
    st.divider()

    # --- FORM NHẬP LIỆU CHÍNH THỨC ---
    with st.form("Form_Nhap_Lieu"):
        st.markdown("#### BƯỚC 2: TIẾN ĐỘ CỬ TRI")
        c1, c2, c3 = st.columns(3)
        with c1: t_ct = st.number_input("Tổng cử tri", min_value=0, step=1)
        with c2: n_ct = st.number_input("Nam", min_value=0, step=1)
        with c3: nu_ct = st.number_input("Nữ", min_value=0, step=1)
        
        st.markdown("#### BƯỚC 3: QUẢN LÝ PHIẾU")
        cau_hinh_hien_tai = MAP_TOA_DO_CHI_TIET[cap_bau_cu]
        
        c4, c5, c6, c7 = st.columns(4)
        with c4: p_phat = st.number_input(f"Phát ra ({cau_hinh_hien_tai['phat']})", min_value=0, step=1)
        with c5: p_thu = st.number_input(f"Thu vào ({cau_hinh_hien_tai['thu']})", min_value=0, step=1)
        with c6: p_hop = st.number_input(f"Hợp lệ ({cau_hinh_hien_tai['hop']})", min_value=0, step=1)
        with c7: p_khong = st.number_input(f"K.Hợp lệ ({cau_hinh_hien_tai['khong']})", min_value=0, step=1)
        
        st.markdown(f"#### BƯỚC 4: KẾT QUẢ KIỂM PHIẾU")
        kq_db = {}
        for db in danh_sach_hien_tai:
            kq_db[db] = st.number_input(f"Số phiếu của: {db}", min_value=0, step=1)
            
        if st.form_submit_button("LƯU & GỬI BÁO CÁO", type="primary"):
            # --- HỆ THỐNG KIỂM TRA CHÉO ĐA LỚP ---
            if t_ct != (n_ct + nu_ct):
                st.error("❌ Lỗi 1: Tổng số cử tri đi bầu không khớp với phép tính (Nam + Nữ)!")
            elif p_thu != (p_hop + p_khong):
                st.error("❌ Lỗi 2: Số phiếu thu vào không khớp với (Hợp lệ + Không hợp lệ)!")
            elif p_thu > p_phat:
                st.error("❌ Lỗi 3: Vô lý! Số phiếu THU VÀO đang lớn hơn số phiếu PHÁT RA!")
            elif p_phat > t_ct:
                st.error("❌ Lỗi 4: Vô lý! Số phiếu PHÁT RA đang lớn hơn TỔNG CỬ TRI đi bầu!")
            else:
                sheet_name = MAP_SHEET[cap_bau_cu]
                
                # --- ĐIỀU HƯỚNG DÒNG (ROW) THÔNG MINH TẠI ĐÂY ---
                if cap_bau_cu == "HĐND phường":
                    h = MAP_HANG_PHUONG.get(st.session_state['ten_to'])
                    if not h:
                        st.error(f"⚠️ Chưa cấu hình dòng cho {st.session_state['ten_to']} cấp Phường.")
                        st.stop()
                else:
                    h = st.session_state['hang_cua_to']

                with st.spinner(f"Đang ghi dữ liệu vào Sheet '{sheet_name}' tại hàng {h}..."):
                    updates = []
                    
                    updates.append({'range': f'{cau_hinh_hien_tai["tong_ct"]}{h}', 'values': [[t_ct]]})
                    updates.append({'range': f'{cau_hinh_hien_tai["nam"]}{h}', 'values': [[n_ct]]})
                    updates.append({'range': f'{cau_hinh_hien_tai["nu"]}{h}', 'values': [[nu_ct]]})

                    updates.append({'range': f'{cau_hinh_hien_tai["phat"]}{h}', 'values': [[p_phat]]})
                    updates.append({'range': f'{cau_hinh_hien_tai["thu"]}{h}', 'values': [[p_thu]]})
                    updates.append({'range': f'{cau_hinh_hien_tai["hop"]}{h}', 'values': [[p_hop]]})
                    updates.append({'range': f'{cau_hinh_hien_tai["khong"]}{h}', 'values': [[p_khong]]})
                    
                    for name, val in kq_db.items():
                        col_letter = cau_hinh_hien_tai["dai_bieu"].get(name)
                        if col_letter:
                            updates.append({'range': f'{col_letter}{h}', 'values': [[val]]})
                    
                    # --- CƠ CHẾ CHỐNG QUÁ TẢI (AUTO-RETRY) ---
                    so_lan_thu_lai = 3
                    thoi_gian_cho = 5 # giây
                    
                    for lan_thu in range(so_lan_thu_lai):
                        try:
                            # Thực hiện ghi đồng loạt tất cả các ô đã trỏ
                            file_du_lieu.worksheet(sheet_name).batch_update(updates)
                            st.success(f"✅ Đã lưu báo cáo thành công vào hàng {h}!")
                            st.balloons()
                            break # Nếu gửi thành công thì thoát ngay khỏi vòng lặp chống tắc đường
                            
                        except Exception as e:
                            thong_diep_loi = str(e).lower()
                            # Bắt lỗi 429 (Too Many Requests) hoặc Quota của Google
                            if "429" in thong_diep_loi or "quota" in thong_diep_loi or "rate limit" in thong_diep_loi:
                                if lan_thu < so_lan_thu_lai - 1:
                                    st.warning(f"⏳ Máy chủ đang xử lý nhiều Tổ cùng lúc. Hệ thống sẽ tự động thử lại sau {thoi_gian_cho} giây... (Lần {lan_thu + 1}/{so_lan_thu_lai})")
                                    time.sleep(thoi_gian_cho)
                                else:
                                    st.error("❌ Mạng đang tắc nghẽn cục bộ do có quá nhiều Tổ cùng gửi. Đồng chí vui lòng đợi khoảng 1 phút rồi bấm nút Gửi lại!")
                            else:
                                # Nếu là lỗi khác (ví dụ sai tên Sheet) thì báo lỗi và dừng luôn
                                st.error(f"❌ Lỗi ghi dữ liệu (Không phải do quá tải): {e}")
                                break

    if st.button("🔒 Đăng xuất"):
        st.session_state.update({'logged_in': False})
        st.rerun()
        
st.markdown("<div style='text-align: center; color: grey; font-size: 14px; margin-top: 30px;'>© 2026 - Bản quyền thuộc Phòng Văn hóa - Xã hội phường Tân Phong</div>", unsafe_allow_html=True)



