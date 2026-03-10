import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 1. CẤU HÌNH KẾT NỐI TỚI GOOGLE SHEETS
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Đọc chìa khóa từ két sắt bảo mật của Streamlit thay vì đọc file .json trên máy
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    client = gspread.authorize(creds)
    return client.open("Solieubaucutanphong") # Đảm bảo tên file đúng

try:
    file_du_lieu = init_connection()
except Exception as e:
    st.error(f"Lỗi kết nối tới cơ sở dữ liệu: {e}")
    st.stop()

# ==========================================
# 2. THIẾT LẬP GIAO DIỆN & TRẠNG THÁI
# ==========================================
st.set_page_config(page_title="Hệ thống Báo cáo Bầu cử - Tân Phong", layout="centered")
st.title("🗳️ Hệ thống Báo cáo Bầu cử - Tân Phong")

# Khởi tạo bộ nhớ tạm để giữ trạng thái đăng nhập
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'ten_to': '', 'hang_cua_to': 0})

# --- THIẾT LẬP HÀNG MỎ NEO ---
HANG_MO_NEO = 6 # Tổ 1 bắt đầu từ hàng số 6 trên Google Sheets

# ==========================================
# 3. MÀN HÌNH ĐĂNG NHẬP DÀNH CHO CÁC TỔ
# ==========================================
if not st.session_state['logged_in']:
    with st.form("Login_Form"):
        st.subheader("Đăng nhập phân quyền")
        
        # Tự động tạo danh sách từ Tổ 1 đến Tổ 46
        danh_sach_to = [f"Tổ {i}" for i in range(1, 47)]
        user_choice = st.selectbox("Chọn đơn vị của bạn", danh_sach_to)
        password_input = st.text_input("Mật khẩu xác thực", type="password")
        
        submit_login = st.form_submit_button("Xác nhận đăng nhập")

        if submit_login:
            # Tách lấy số thứ tự (Ví dụ: "Tổ 2" -> Lấy số 2)
            so_thu_tu_to = int(user_choice.replace("Tổ ", ""))
            
            # Tính toán hàng thực tế: Hàng = Mỏ neo + (STT - 1)
            hang_thuc_te = HANG_MO_NEO + (so_thu_tu_to - 1)
            
            try:
                # Đọc mật khẩu từ Cột B (Cột 2) của sheet "Quoc Hoi" để đối chiếu
                sheet_check = file_du_lieu.worksheet("Quoc Hoi")
                mat_khau_he_thong = sheet_check.cell(hang_thuc_te, 2).value 
                
                if str(password_input) == str(mat_khau_he_thong):
                    st.session_state['logged_in'] = True
                    st.session_state['ten_to'] = user_choice
                    st.session_state['hang_cua_to'] = hang_thuc_te
                    st.rerun() # Tải lại trang để vào giao diện chính
                else:
                    st.error("Sai mật khẩu! Vui lòng kiểm tra lại.")
            except Exception as e:
                st.error(f"Lỗi khi đọc mật khẩu từ hệ thống: {e}")

# ==========================================
# 4. MÀN HÌNH NHẬP LIỆU BÁO CÁO CỬ TRI
# ==========================================
else:
    st.success(f"Chào mừng đại diện **{st.session_state['ten_to']}**!")
    st.info(f"📍 Dữ liệu của bạn sẽ được trỏ chính xác vào **Hàng số {st.session_state['hang_cua_to']}** trên hệ thống.")

    # Menu chọn Cấp bầu cử
    cap_bau_cu = st.selectbox(
        "Vui lòng chọn cấp bầu cử bạn muốn báo cáo:", 
        ["Quoc Hoi", "HDND Tinh", "HDND Huyen", "HDND Xa"]
    )

    try:
        sheet_hien_tai = file_du_lieu.worksheet(cap_bau_cu)
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Lỗi: Không tìm thấy trang tính '{cap_bau_cu}'. Vui lòng tạo đúng tên trang tính trên Google Sheets.")
        st.stop()

    # Form nhập liệu chính
    with st.form("Data_Entry_Form"):
        st.write("### Cập nhật tiến độ cử tri đi bầu")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            tong_cu_tri = st.number_input("Tổng số cử tri (Ô J)", min_value=0, step=1)
        with col2:
            cu_tri_nam = st.number_input("Cử tri Nam (Ô K)", min_value=0, step=1)
        with col3:
            cu_tri_nu = st.number_input("Cử tri Nữ (Ô L)", min_value=0, step=1)
        
        submit_data = st.form_submit_button("Lưu số liệu", type="primary")

        if submit_data:
            # --- KIỂM TRA CHÉO LOGIC ---
            if tong_cu_tri != (cu_tri_nam + cu_tri_nu):
                st.error("⚠️ Lỗi dữ liệu: Tổng số cử tri không khớp với phép tính (Nam + Nữ). Vui lòng kiểm tra lại!")
            else:
                # Nếu số liệu logic, tiến hành gom mảng để bắn lên Google Sheets
                du_lieu_cu_tri = [[tong_cu_tri, cu_tri_nam, cu_tri_nu]]
                
                hang_hien_tai = st.session_state['hang_cua_to']
                # Tạo tọa độ động (Ví dụ: J6:L6, J7:L7...)
                vung_cap_nhat = f"J{hang_hien_tai}:L{hang_hien_tai}"
                
                try:
                    sheet_hien_tai.update(vung_cap_nhat, du_lieu_cu_tri)
                    st.balloons()
                    st.success(f"✅ Đã trỏ thành công số liệu vào tọa độ **{vung_cap_nhat}** của cấp {cap_bau_cu}!")
                except Exception as e:
                    st.error(f"Lỗi đường truyền khi lưu dữ liệu: {e}")

    # Nút đăng xuất an toàn
    st.divider()
    if st.button("Đăng xuất"):
        st.session_state['logged_in'] = False
        st.rerun()