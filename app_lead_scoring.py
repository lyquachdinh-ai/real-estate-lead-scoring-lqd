import pandas as pd
import requests
import re
import streamlit as st
from io import BytesIO

# --- Cấu hình trang Streamlit ---
st.set_page_config(page_title="Hệ thống AI Lead Scoring - Bất động sản", layout="wide")

# --- Định nghĩa các quy tắc chấm điểm (Dựa trên lead_scoring_skill.md) ---
RULES = {
    "VIP": {
        "keywords": [
            r"tài chính mạnh", r"không thành vấn đề", r"thanh toán thẳng", r"ngân sách lớn",
            r"biệt thự đơn lập", r"penthouse", r"shophouse", r"quỹ đất công nghiệp", r"sàn văn phòng diện tích lớn",
            r"quận 1", r"ven sông", r"vinhomes", r"phú mỹ hưng",
            r"chủ doanh nghiệp", r"nhà đầu tư chuyên nghiệp", r"mua sỉ", r"mua số lượng lớn",
            r"pháp lý chuẩn", r"sổ hồng riêng", r"gặp trực tiếp chủ đầu tư"
        ],
        "score": 50
    },
    "TRASH": {
        "keywords": [
            r"nhầm số", r"không có nhu cầu", r"dữ liệu cũ", r"nhầm ngành",
            r"hỏi giá cho vui", r"chưa có ý định mua", r"thái độ không hợp tác",
            r"bảo hiểm", r"vay vốn", r"mời chào dịch vụ", r"quảng cáo",
            r"thuê bao", r"không bắt máy", r"không phản hồi zalo"
        ],
        "score": -50
    }
}

def calculate_score(description):
    """Hàm chấm điểm dựa trên mô tả nhu cầu"""
    if not isinstance(description, str):
        return 0, "Trung bình", "Không có mô tả nhu cầu"
    
    desc_lower = description.lower()
    score = 0
    reasons = []

    # Kiểm tra quy tắc Rác trước (Ưu tiên theo lead_scoring_skill.md)
    trash_found = [kw for kw in RULES["TRASH"]["keywords"] if re.search(kw, desc_lower)]
    
    # Kiểm tra yêu cầu phi thực tế (Giá rẻ khu đắt tiền)
    unrealistic_check = re.search(r"quận 1.*(1|2|vài trăm).*tỷ", desc_lower) or \
                        re.search(r"trung tâm.*(2|hai).*triệu", desc_lower)
    
    if trash_found or unrealistic_check:
        score = -50
        reason_text = "Dấu hiệu rác: " + ", ".join(trash_found)
        if unrealistic_check:
            reason_text += " | Yêu cầu phi thực tế"
        return score, "Rác", reason_text

    # Kiểm tra quy tắc VIP
    vip_found = [kw for kw in RULES["VIP"]["keywords"] if re.search(kw, desc_lower)]
    
    # Kiểm tra ngân sách >= 20 tỷ
    budget_match = re.search(r"(\d+)\s*tỷ", desc_lower)
    if budget_match:
        budget = int(budget_match.group(1))
        if budget >= 20:
            vip_found.append(f"Ngân sách {budget} tỷ")

    if vip_found:
        score = 50
        return score, "VIP", "Dấu hiệu VIP: " + ", ".join(vip_found)

    # Các trường hợp khác
    return 0, "Trung bình", "Nhu cầu thực tế, cần tư vấn thêm"

def load_data(url):
    """Tải dữ liệu từ Google Sheets công khai"""
    try:
        # Chuyển đổi link edit sang link export CSV
        csv_url = url.replace('/edit?gid=', '/export?format=csv&gid=')
        if '/export' not in csv_url:
            csv_url = url.split('/edit')[0] + '/export?format=csv'
            
        response = requests.get(csv_url)
        response.encoding = 'utf-8'
        df = pd.read_csv(BytesIO(response.content))
        return df
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
        return None

# --- Giao diện chính ---
st.title("🏙️ AI Lead Scoring Automation System")
st.markdown("---")

# Sidebar cấu hình
st.sidebar.header("Cấu hình nguồn dữ liệu")
sheet_url = st.sidebar.text_input("Google Sheet URL", "https://docs.google.com/spreadsheets/d/1vjkil0YX-o33KebjTQSB2dHDeydDg2ZpHxheJkQ8Vkk/edit?gid=0#gid=0")

if st.sidebar.button("Tải & Chấm điểm dữ liệu"):
    with st.spinner("Đang xử lý dữ liệu bằng AI..."):
        df = load_data(sheet_url)
        
        if df is not None:
            # Thực hiện chấm điểm
            results = df.apply(lambda row: calculate_score(row['nhu_cau_mo_ta']), axis=1)
            df['Diem'], df['Phan_loai'], df['Ly_do'] = zip(*results)
            
            st.session_state['data'] = df
            st.success(f"Đã xử lý xong {len(df)} khách hàng!")

# Hiển thị kết quả
if 'data' in st.session_state:
    df = st.session_state['data']
    
    # Bộ lọc nhanh
    col1, col2 = st.columns(2)
    with col1:
        filter_class = st.multiselect("Lọc theo phân loại", options=["VIP", "Tiềm năng", "Trung bình", "Rác"], default=["VIP", "Tiềm năng", "Trung bình", "Rác"])
    
    filtered_df = df[df['Phan_loai'].isin(filter_class)]
    
    # Hiển thị bảng kết quả
    st.subheader("Bảng danh sách khách hàng đã chấm điểm")
    
    # Tạo màu sắc cho phân loại
    def color_classify(val):
        color = 'white'
        if val == 'VIP': color = '#d4edda' # Xanh lá nhẹ
        elif val == 'Rác': color = '#f8d7da' # Đỏ nhẹ
        elif val == 'Trung bình': color = '#fff3cd' # Vàng nhẹ
        return f'background-color: {color}'

    st.dataframe(filtered_df.style.applymap(color_classify, subset=['Phan_loai']), use_container_width=True)

    # Xuất dữ liệu Excel
    st.markdown("---")
    st.subheader("📥 Xuất báo cáo")
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Lead_Scoring_Results')
    
    st.download_button(
        label="Tải file Excel kết quả (.xlsx)",
        data=output.getvalue(),
        file_name="lead_scoring_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Vui lòng nhấn nút 'Tải & Chấm điểm dữ liệu' ở thanh bên trái để bắt đầu.")

# Hướng dẫn
with st.expander("ℹ️ Hướng dẫn về thuật toán chấm điểm"):
    st.markdown("""
    Hệ thống sử dụng các quy tắc từ `lead_scoring_skill.md`:
    - **VIP (+50):** Nhận diện từ khóa tài chính mạnh, sản phẩm Penthouse/Biệt thự, hoặc ngân sách thực tế >= 20 tỷ.
    - **Rác (-50):** Nhận diện các từ khóa 'nhầm số', 'spam', 'quảng cáo' hoặc các yêu cầu giá thấp vô lý (VD: Nhà trung tâm giá 2 triệu).
    - **Trung bình (0):** Các nhu cầu thực tế ở phân khúc 3-10 tỷ nhưng chưa có dấu hiệu VIP.
    """)
