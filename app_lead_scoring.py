import pandas as pd
import requests
import re
import streamlit as st
from io import BytesIO

# --- Cấu hình trang Streamlit ---
st.set_page_config(
    page_title="AI Lead Scoring System - Real Estate",
    page_icon="🏙️",
    layout="wide"
)

# --- CSS tùy chỉnh để làm đẹp giao diện ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Định nghĩa bộ quy tắc chấm điểm nâng cao (Dựa trên lead_scoring_skill.md) ---
RULES = {
    "VIP": {
        "keywords": [
            r"tài chính mạnh", r"không thành vấn đề", r"thanh toán thẳng", r"ngân sách lớn",
            r"biệt thự đơn lập", r"penthouse", r"shophouse", r"quỹ đất công nghiệp", r"sàn văn phòng diện tích lớn",
            r"quận 1", r"ven sông", r"vinhomes", r"phú mỹ hưng", r"thanh toán 100%", r"mua sỉ", r"số lượng lớn",
            r"chủ doanh nghiệp", r"nhà đầu tư chuyên nghiệp", r"pháp lý chuẩn", r"sổ hồng riêng", r"gặp chủ đầu tư"
        ],
        "score": 50
    },
    "TRASH": {
        "keywords": [
            r"nhầm số", r"không có nhu cầu", r"dữ liệu cũ", r"nhầm ngành", r"sai số",
            r"hỏi giá cho vui", r"chưa có ý định mua", r"thái độ không hợp tác",
            r"bảo hiểm", r"vay vốn", r"mời chào dịch vụ", r"quảng cáo", r"spam",
            r"thuê bao", r"không bắt máy", r"không phản hồi", r"chặn zalo"
        ],
        "score": -50
    }
}

def calculate_score(description):
    """Hàm chấm điểm dựa trên mô tả nhu cầu (Rule-based AI)"""
    if not isinstance(description, str) or description.strip() == "":
        return 0, "Trung bình", "Không có thông tin mô tả"
    
    desc_lower = description.lower()
    score = 0
    reasons = []

    # 1. Kiểm tra dấu hiệu Rác (Ưu tiên loại bỏ)
    trash_found = [kw for kw in RULES["TRASH"]["keywords"] if re.search(kw, desc_lower)]
    
    # Kiểm tra yêu cầu phi thực tế (Ví dụ: Nhà Q1 giá quá thấp)
    unreal_q1 = re.search(r"(quận 1|q1).* (1|2|vài).* tỷ", desc_lower)
    unreal_center = re.search(r"trung tâm.* (2|hai).* triệu", desc_lower)
    
    if trash_found or unreal_q1 or unreal_center:
        reason_list = trash_found
        if unreal_q1 or unreal_center:
            reason_list.append("Yêu cầu phi thực tế về giá/vị trí")
        return -50, "Rác", "Dấu hiệu không tiềm năng: " + ", ".join(reason_list)

    # 2. Kiểm tra dấu hiệu VIP
    vip_found = [kw for kw in RULES["VIP"]["keywords"] if re.search(kw, desc_lower)]
    
    # Kiểm tra ngân sách >= 20 tỷ bằng số
    budget_match = re.search(r"(\d+)\s*tỷ", desc_lower)
    if budget_match:
        val = int(budget_match.group(1))
        if val >= 20:
            vip_found.append(f"Ngân sách lớn ({val} tỷ)")

    if vip_found:
        return 50, "VIP", "Tiềm năng cao: " + ", ".join(vip_found)

    # 3. Các trường hợp còn lại
    return 0, "Trung bình", "Nhu cầu thực tế, cần theo dõi thêm"

def load_data(source_type, source_val):
    """Tải dữ liệu từ Google Sheets hoặc File Upload"""
    try:
        if source_type == "Google Sheets":
            csv_url = source_val.replace('/edit?gid=', '/export?format=csv&gid=')
            if '/export' not in csv_url:
                csv_url = source_val.split('/edit')[0] + '/export?format=csv'
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(csv_url, headers=headers)
            response.encoding = 'utf-8'
            df = pd.read_csv(BytesIO(response.content))
        else:
            if source_val.name.endswith('.csv'):
                df = pd.read_csv(source_val)
            else:
                df = pd.read_excel(source_val)
        
        # Chuẩn hóa tên cột (Tìm cột chứa mô tả nhu cầu)
        target_col = None
        for col in df.columns:
            if 'nhu_cau' in col.lower() or 'mo_ta' in col.lower() or 'description' in col.lower():
                target_col = col
                break
        
        if target_col:
            df = df.rename(columns={target_col: 'nhu_cau_mo_ta'})
        else:
            st.error("⚠️ Không tìm thấy cột mô tả nhu cầu. Vui lòng kiểm tra lại file.")
            return None
            
        return df
    except Exception as e:
        st.error(f"❌ Lỗi tải dữ liệu: {e}")
        return None

# --- UI Header ---
st.title("🏙️ AI Lead Scoring & Automation")
st.subheader("Hệ thống chấm điểm khách hàng tiềm năng - Real Estate Edition")
st.markdown("---")

# --- Sidebar ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1680/1680951.png", width=100)
st.sidebar.header("📥 Nguồn Dữ Liệu")
input_method = st.sidebar.radio("Chọn phương thức nhập:", ["Google Sheets", "Tải file lên (CSV/Excel)"])

source_input = None
if input_method == "Google Sheets":
    source_input = st.sidebar.text_input("Dán link Google Sheet:", "https://docs.google.com/spreadsheets/d/1vjkil0YX-o33KebjTQSB2dHDeydDg2ZpHxheJkQ8Vkk/edit?gid=0#gid=0")
else:
    source_input = st.sidebar.file_uploader("Chọn file dữ liệu:", type=['csv', 'xlsx'])

process_btn = st.sidebar.button("🚀 Bắt đầu chấm điểm")

# --- Main Logic ---
if process_btn and source_input:
    with st.spinner("Đang phân tích dữ liệu bằng thuật toán Lead Scoring..."):
        df = load_data(input_method, source_input)
        
        if df is not None:
            # Thực hiện chấm điểm
            results = df.apply(lambda row: calculate_score(row['nhu_cau_mo_ta']), axis=1)
            df['Diem'], df['Phan_loai'], df['Ly_do'] = zip(*results)
            
            st.session_state['data'] = df
            st.success(f"✅ Đã xử lý thành công {len(df)} bản ghi!")

# --- Hiển thị kết quả ---
if 'data' in st.session_state:
    df = st.session_state['data']
    
    # Dashboard Thống kê
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng Lead", len(df))
    m2.metric("Khách VIP 💎", len(df[df['Phan_loai'] == 'VIP']))
    m3.metric("Trung bình 🟡", len(df[df['Phan_loai'] == 'Trung bình']))
    m4.metric("Loại bỏ (Rác) 🔴", len(df[df['Phan_loai'] == 'Rác']))
    
    # Bộ lọc & Bảng dữ liệu
    st.markdown("### 🔍 Chi Tiết Danh Sách")
    f_col = st.multiselect("Lọc trạng thái:", ["VIP", "Trung bình", "Rác"], default=["VIP", "Trung bình", "Rác"])
    
    view_df = df[df['Phan_loai'].isin(f_col)]
    
    # Styling Table
    def color_rows(val):
        color = 'white'
        if val == 'VIP': color = '#d4edda'
        elif val == 'Rác': color = '#f8d7da'
        elif val == 'Trung bình': color = '#fff3cd'
        return f'background-color: {color}'

    try:
        styled_df = view_df.style.map(color_rows, subset=['Phan_loai'])
    except:
        styled_df = view_df.style.applymap(color_rows, subset=['Phan_loai'])
        
    st.dataframe(styled_df, use_container_width=True)

    # Export
    st.markdown("---")
    col_dl1, col_dl2 = st.columns([1, 4])
    with col_dl1:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='LeadScoring')
        
        st.download_button(
            label="💾 Tải File Bàn Giao (.xlsx)",
            data=output.getvalue(),
            file_name="Bao_Cao_Cham_Diem_Lead.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col_dl2:
        st.info("💡 File Excel tải về đã bao gồm đầy đủ cột Điểm, Phân loại và Lý do chi tiết để bạn gửi cho khách hàng/sếp.")

else:
    st.info("👋 Chào mừng! Vui lòng chọn nguồn dữ liệu ở thanh bên trái và nhấn nút 'Bắt đầu chấm điểm'.")

# Footer
st.markdown("---")
st.caption("AI Lead Scoring System v1.2 | Phát triển dựa trên Quy tắc nghiệp vụ Bất động sản")
