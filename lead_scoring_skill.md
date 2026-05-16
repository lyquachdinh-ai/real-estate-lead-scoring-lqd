---
name: Lead Scoring AI Skill
description: Hệ thống AI tự động chấm điểm khách hàng tiềm năng ngành Bất động sản dựa trên mô tả nhu cầu và quy tắc nghiệp vụ.
---

# Lead Scoring AI Skill (Bất động sản)

## 🎯 Mục tiêu
Tự động hóa việc phân loại và chấm điểm khách hàng (Lead Scoring) từ dữ liệu mô tả nhu cầu để giúp đội ngũ kinh doanh ưu tiên chăm sóc các khách hàng tiềm năng nhất (VIP) và loại bỏ các dữ liệu rác.

## 📥 Đầu vào (Input)
Dữ liệu khách hàng thường có cấu trúc:
- `id`: Mã khách hàng.
- `ten_khach`: Họ tên khách hàng.
- `sdt`: Số điện thoại.
- `nhu_cau_mo_ta`: Đoạn văn bản mô tả nhu cầu, tình trạng hoặc lịch sử tương tác.

## 📤 Đầu ra (Output)
Bảng kết quả bao gồm:
- `id`, `ten_khach`, `sdt`.
- `Diem`: Điểm số (Mặc định 0, cộng/trừ theo quy tắc).
- `Phan_loai`: (VIP / Tiềm năng / Trung bình / Rác).
- `Ly_do`: Giải thích ngắn gọn tại sao chấm điểm như vậy.

## 🛠 Quy trình thực hiện (Workflow)

### Bước 1: Trích xuất thông tin
AI đọc trường `nhu_cau_mo_ta` để tìm kiếm các thực thể:
- **Ngân sách**: Số tiền cụ thể hoặc từ khóa về tài chính.
- **Loại hình BĐS**: Chung cư, nhà phố, biệt thự, penthouse, đất nền...
- **Vị trí**: Quận/Huyện, tên dự án.
- **Đối tượng**: Cá nhân, chủ doanh nghiệp, nhà đầu tư...
- **Tình trạng**: Thiện chí, spam, không liên lạc được...

### Bước 2: Áp dụng quy tắc chấm điểm (Scoring Rules)

#### 🟢 Cộng 50 điểm (Khách hàng VIP)
Nếu thỏa mãn ít nhất một trong các điều kiện:
- **Tài chính cực mạnh**: Ngân sách >= 20 tỷ, hoặc từ khóa "tài chính mạnh", "ngân sách không thành vấn đề", "thanh toán thẳng".
- **Sản phẩm cao cấp**: "Biệt thự đơn lập", "Penthouse", "Shophouse mặt đường lớn", "Quỹ đất công nghiệp", "Sàn văn phòng diện tích lớn".
- **Vị trí đắc địa**: "Quận 1", "Ven sông", "Vinhomes Ocean Park", "Phú Mỹ Hưng".
- **Chân dung khách hàng**: "Chủ doanh nghiệp", "Nhà đầu tư chuyên nghiệp", "Mua sỉ", "Mua số lượng lớn".
- **Tính pháp lý & Cấp thiết**: "Pháp lý chuẩn 100%", "Sổ hồng riêng", "Gặp trực tiếp chủ đầu tư".

#### 🔴 Trừ 50 điểm (Khách hàng Rác/Không tiềm năng)
Nếu thỏa mãn ít nhất một trong các điều kiện:
- **Yêu cầu phi thực tế**: Tìm giá thấp vô lý (VD: Nhà Q1 giá 1-2 tỷ, nhà trung tâm có sân vườn giá vài trăm triệu).
- **Không có nhu cầu**: "Nhầm số", "Dữ liệu cũ", "Nhầm ngành".
- **Thiếu thiện chí**: "Hỏi giá cho vui", "Chưa có ý định mua", "Thái độ không hợp tác".
- **Spam/Quảng cáo**: Chứa nội dung "Bảo hiểm", "Vay vốn", "Mời chào dịch vụ".
- **Lỗi liên lạc**: "Thuê bao", "Gọi không bắt máy", "Không phản hồi Zalo".

#### 🟡 Giữ nguyên điểm (0 - 10 điểm) - Khách hàng Trung bình
- Tìm mua chung cư, nhà phố tầm trung (3-10 tỷ).
- Cần vay ngân hàng, đang cân nhắc.
- Có nhu cầu thực nhưng cần tư vấn thêm nhiều.

### Bước 3: Tổng hợp & Phân loại
- **Điểm >= 50**: Phân loại **VIP**.
- **0 < Điểm < 50**: Phân loại **Tiềm năng**.
- **Điểm == 0**: Phân loại **Trung bình**.
- **Điểm < 0**: Phân loại **Rác**.

## ⚖️ Quy tắc AI (Rules)
1. **Context Matters**: Phải đọc hết ngữ cảnh, không chỉ dựa vào từ khóa đơn lẻ. Ví dụ: "Tìm nhà Q1 giá 1 tỷ" -> Trừ điểm (Phi thực tế), nhưng "Ngân sách 20 tỷ tìm nhà Q1" -> Cộng điểm (VIP).
2. **Logic ưu tiên**: Nếu vừa có dấu hiệu VIP vừa có dấu hiệu Rác (Ví dụ: Đại gia nhưng nhầm số), ưu tiên phân loại theo tình trạng thực tế là **Rác**.
3. **Giải thích**: Phần `Ly_do` phải ghi rõ từ khóa hoặc dấu hiệu cụ thể dẫn đến điểm số đó.

## 📝 Ví dụ minh họa
| Mô tả | Điểm | Phân loại | Lý do |
| :--- | :--- | :--- | :--- |
| "Chủ doanh nghiệp tìm biệt thự đơn lập Ven sông, tài chính 50 tỷ." | 50 | VIP | Khách hàng là chủ DN, tìm sản phẩm cao cấp, ngân sách lớn. |
| "Muốn mua nhà Quận 1 giá 500 triệu để ở." | -50 | Rác | Yêu cầu phi thực tế (giá quá thấp so với khu vực). |
| "Quan tâm căn hộ 2PN Quận 7, tài chính 4 tỷ, cần vay bank." | 0 | Trung bình | Nhu cầu thực tế tầm trung, cần hỗ trợ tài chính. |
