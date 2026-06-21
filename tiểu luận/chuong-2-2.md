**2.2. Kịch bản tích hợp AI Agent vào hệ thống BI SeABank**

Để giải quyết tình trạng quá tải trong việc trích xuất báo cáo thủ công, SeABank định hướng triển khai trợ lý ảo nội bộ mang tên "SeA-Analyst". Chức năng cốt lõi của SeA-Analyst là cho phép các cấp quản lý (ví dụ: Giám đốc chi nhánh) tra cứu nhanh các chỉ số kinh doanh như doanh thu, tỷ lệ nợ xấu, hay dư nợ tín dụng trực tiếp bằng ngôn ngữ tự nhiên thông qua giao diện chat.

Về mặt kỹ thuật, SeA-Analyst được thiết kế dựa trên kiến trúc RAG (Retrieval-Augmented Generation) kết hợp với khả năng gọi hàm (Function Calling). Khi một Giám đốc đặt câu hỏi: *"Tổng nợ xấu nhóm 3 của chi nhánh tháng này là bao nhiêu?"*, luồng xử lý không đi thẳng từ người dùng vào cơ sở dữ liệu mà bị chia tách qua các bước trung gian.

Đầu tiên, câu hỏi được truy xuất ngữ cảnh từ một Vector Database nội bộ. Cơ sở dữ liệu này chứa các tài liệu nghiệp vụ tĩnh (quy chế, định nghĩa chỉ số) đã được nhúng (embedding) sẵn, giúp mô hình ngôn ngữ lớn (LLM) hiểu chính xác khái niệm "nợ xấu nhóm 3" theo quy chuẩn riêng của ngân hàng. 

Sau khi xác định được ngữ cảnh nghiệp vụ, AI Agent sẽ chủ động khởi tạo một lời gọi API (API request) hướng thẳng vào lõi phân tích của Oracle Analytics Server (OAS) để lấy dữ liệu động (real-time data). Lúc này, Agent đóng vai trò như một phần mềm trung gian tự trị: nó yêu cầu OAS chạy lệnh SQL để trích xuất số liệu thực tế từ cơ sở dữ liệu vật lý. Cuối cùng, OAS trả dữ liệu thô về cho Agent, và LLM sẽ tổng hợp lại thành một câu trả lời ngôn ngữ tự nhiên hoàn chỉnh trên màn hình người dùng.

Kịch bản RAG này giải quyết xuất sắc bài toán tối ưu hóa thời gian tra cứu. Mặc dù vậy, việc một phần mềm thứ ba đứng ra làm trung gian dịch mã và tự động truy xuất dữ liệu xuyên hệ thống đã vô tình tạo ra một đường ống (pipeline) đâm xuyên qua các lớp phòng thủ truyền thống. Sự dịch chuyển từ mô hình "con người trực tiếp kéo dữ liệu" sang "Agent tự chủ truy xuất thay người" chính là khởi nguồn cho các lỗ hổng kiến trúc nghiêm trọng.
