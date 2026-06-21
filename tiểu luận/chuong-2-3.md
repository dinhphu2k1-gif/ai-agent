**2.3. Nhận diện nguy cơ phá vỡ kiến trúc bảo mật (The Security Gap)**

Sự chuyển dịch từ mô hình truy vấn thủ công sang tự động hóa thông qua AI Agent tại SeABank làm nảy sinh ba lỗ hổng kiến trúc đặc thù. Nếu không thiết lập các rào chắn kỹ thuật tương xứng, những lỗ hổng này có khả năng làm sụp đổ toàn bộ cơ sở kiểm soát truy cập đã trình bày ở mục 2.1.

**Lỗ hổng thứ nhất: Vô hiệu hóa RLS thông qua Service Account**
Để AI Agent có khả năng giao tiếp liên tục với Oracle Analytics Server (OAS), cách tiếp cận dễ dãi nhất về mặt kỹ thuật là gán cho nó một "tài khoản dịch vụ" (Service Account) mang đặc quyền cao (ví dụ: Read-All). 

Hệ lụy trực tiếp của phương pháp này là cơ chế Row-Level Security (RLS) bị vô hiệu hóa hoàn toàn. OAS lúc này chỉ nhận diện duy nhất định danh của Service Account mà không biết được danh tính thực sự của nhân viên đang tương tác với AI. Các thuật toán cắt tỉa dữ liệu cấp dòng (row-level filtering) không có điểm tựa để kích hoạt. Hậu quả là một chuyên viên tín dụng cấp thấp hoàn toàn có thể dùng kỹ thuật kỹ sư câu lệnh (Prompt Engineering) để ép AI Agent trích xuất báo cáo lương của cấp lãnh đạo – điều bất khả thi trên giao diện OAS thông thường.

**Lỗ hổng thứ hai: Rò rỉ dữ liệu nhạy cảm (PII) qua RAG Pipeline**
Kiến trúc RAG đòi hỏi quá trình trích xuất dữ liệu từ Oracle Database, nhúng (embedding) và đồng bộ sang Vector Database để phục vụ việc tra cứu ngữ cảnh. Điểm mù bảo mật nằm ngay tại khâu dịch chuyển dữ liệu (ETL) này. 

Khi dữ liệu rời khỏi ranh giới của cơ sở dữ liệu gốc, toàn bộ các nhãn bảo mật (security tags) và quy tắc phân quyền định sẵn sẽ bị gột rửa (strip off). Bản chất Vector Database được thiết kế tối ưu cho thuật toán tìm kiếm tương đồng (similarity search), không sở hữu cơ chế phân quyền hạt nhân phức tạp như Oracle. Nếu luồng đồng bộ vô tình đưa các thông tin định danh cá nhân (PII) như tên khách hàng, số CCCD, hay sao kê giao dịch lên Vector Database, AI Agent có thể dễ dàng truy xuất và phơi bày các thông tin này cho bất kỳ ai đặt câu hỏi truy vấn.

**Lỗ hổng thứ ba: Phình to phạm vi truy cập (Data Scope Creep)**
Không giống như các lệnh API truyền thống chỉ trả về một cấu trúc JSON cố định, AI Agent có tính tự trị cao trong việc lập luận và tự động sinh mã SQL. Khi một Giám đốc yêu cầu: *"Tính tỷ lệ nợ xấu của chi nhánh"*, AI Agent có thể tự động quyết định quét (scan) toàn bộ lịch sử giao dịch, thông tin thế chấp và hồ sơ cá nhân của khách hàng chỉ để tổng hợp ra một con số duy nhất.

Hành vi này gây ra hiện tượng "Data Scope Creep" – Agent chạm vào lượng dữ liệu lớn hơn gấp nhiều lần so với mức độ tối thiểu cần thiết để giải quyết tác vụ. Việc lạm dụng quyền đọc (Read-access abuse) không chỉ gây tắc nghẽn tài nguyên máy chủ phân tích, mà còn làm phình to bề mặt tấn công. Nếu bị chiếm quyền điều khiển (hijacked), kẻ tấn công có thể lợi dụng đặc tính quét rộng này để đánh cắp (exfiltrate) toàn bộ kho dữ liệu cốt lõi thông qua một vài câu lệnh chat có vỏ bọc vô hại.
