### CHƯƠNG 5: THỰC NGHIỆM TRIỂN KHAI (Proof of Concept)

**5.1. Kiến trúc hệ thống thực nghiệm và lựa chọn công nghệ**

Toàn bộ kiến trúc bảo mật đề xuất ở Chương 3 sẽ không có sức thuyết phục nếu chỉ dừng lại trên lý thuyết. Chương này hiện thực hóa các cơ chế PBAC, OBO Token Flow, và bộ lọc RAG 3 lớp thành một hệ thống demo có khả năng vận hành thực tế, nhằm kiểm chứng tính khả thi kỹ thuật trước khi đề xuất triển khai trên môi trường production của SeABank.

Do hạ tầng Oracle Analytics Server (OAS) thực tế của ngân hàng không thể truy cập cho mục đích thí nghiệm, hệ thống demo được xây dựng trên các công nghệ mã nguồn mở có cơ chế tương đương, đảm bảo mô phỏng chính xác luồng phân quyền và kiểm soát dữ liệu mà không hy sinh tính chân thực của kịch bản.

Kiến trúc tổng thể của hệ thống thực nghiệm bao gồm 7 thành phần cốt lõi, được đóng gói và cô lập trong các container Docker riêng biệt, kết nối với nhau thông qua một mạng nội bộ (internal Docker network) có kiểm soát luồng ra (egress control):

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Compose Network (internal)                │
│                                                                     │
│  ┌──────────┐    ┌───────────┐    ┌──────────────────────────────┐  │
│  │  Chat UI │───▶│ Keycloak  │    │   Agent Backend (FastAPI)    │  │
│  │ (React)  │    │   (IdP)   │───▶│  ┌────────┐  ┌───────────┐  │  │
│  └──────────┘    └───────────┘    │  │LangChain│  │ Presidio  │  │  │
│                                   │  └────┬───┘  └───────────┘  │  │
│                                   │       │                      │  │
│                                   │  ┌────▼───────────────────┐  │  │
│                                   │  │  Guardrails AI (Filter)│  │  │
│                                   │  └────────────────────────┘  │  │
│                                   └──────────┬───────────────────┘  │
│                                              │                      │
│                          ┌───────────────────┼──────────────┐       │
│                          │                   │              │       │
│                    ┌─────▼─────┐    ┌────────▼───┐  ┌───────▼────┐  │
│                    │ ChromaDB  │    │ PostgreSQL │  │ API Gateway│  │
│                    │ (Vector)  │    │   (RLS)    │  │  (Kong)    │  │
│                    └───────────┘    └────────────┘  └────────────┘  │
│                                                                     │
│                         ✕ Internet Egress: BLOCKED                  │
└─────────────────────────────────────────────────────────────────────┘
```

Dưới đây là phân tích lý do lựa chọn từng thành phần công nghệ:

**Keycloak — Identity Provider (IdP)**
Keycloak là nền tảng quản lý định danh mã nguồn mở do Red Hat phát triển. Lý do cốt lõi để chọn Keycloak nằm ở khả năng hỗ trợ gốc (native) giao thức OAuth 2.0 Token Exchange theo chuẩn RFC 8693. Đây là tính năng bắt buộc để hiện thực hóa luồng On-Behalf-Of (OBO): Keycloak tiếp nhận Access Token gốc của người dùng và trao đổi thành một OBO Token mới với `scope` bị thu hẹp, truyền thẳng cho AI Agent. Ngoài ra, Keycloak cung cấp giao diện quản trị trực quan để cấu hình Realm, Client, và phân quyền nhóm người dùng (Role Mapping), mô phỏng sát nhất cơ chế Active Directory của SeABank.

**LangChain / LangGraph — AI Agent Framework**
LangChain (Python) đóng vai trò bộ điều phối trung tâm (orchestrator) cho toàn bộ luồng suy luận của AI Agent. Framework này cho phép định nghĩa chuỗi hành động (chain) bao gồm: nhận câu hỏi → truy xuất ngữ cảnh từ Vector Database → gọi Function Calling để sinh truy vấn SQL → tổng hợp kết quả thành câu trả lời. LangGraph bổ sung khả năng xây dựng luồng xử lý dạng đồ thị có trạng thái (stateful graph), phù hợp để mô hình hóa các bước kiểm tra bảo mật trước và sau mỗi hành động của Agent.

**Google Gemini API — Mô hình ngôn ngữ lớn (LLM)**
Gemini API được sử dụng làm bộ não xử lý ngôn ngữ tự nhiên, chịu trách nhiệm phân tích câu hỏi của người dùng, sinh mã SQL tương ứng, và tổng hợp dữ liệu thô thành câu trả lời hoàn chỉnh. Gemini hỗ trợ Function Calling gốc, cho phép Agent gọi các hàm truy vấn dữ liệu một cách có cấu trúc thay vì tự do sinh mã bất kiểm soát.

**ChromaDB — Vector Database**
ChromaDB được chọn vì tính nhẹ gọn và khả năng hỗ trợ Metadata Filtering gốc. Khi nạp các vector chunk vào ChromaDB, hệ thống đồng thời gắn kèm các thẻ siêu dữ liệu (metadata tags) như `branch_id` và `clearance_level`. Tại bước truy vấn, thuật toán tìm kiếm tương đồng sẽ bị ép thêm bộ lọc cứng (hard filter) dựa trên thông tin trích xuất từ OBO Token, đảm bảo Agent chỉ chạm được vào các chunk thuộc phạm vi quyền hạn của người dùng.

**FastAPI + Kong — API Gateway & Policy Enforcement**
FastAPI middleware tự xây đóng vai trò điểm kiểm soát trung tâm (Policy Enforcement Point) theo nguyên tắc Zero Trust. Mỗi lời gọi API từ Agent đều bị middleware can thiệp để: (1) giải mã và xác minh OBO Token, (2) đối chiếu `scope` trong token với hành động API được yêu cầu, (3) từ chối mọi yêu cầu mang tính thay đổi trạng thái (INSERT/UPDATE/DELETE). Kong Gateway bổ sung khả năng rate-limiting và ghi log tập trung.

**Microsoft Presidio — Data Masking**
Presidio là thư viện mã nguồn mở do Microsoft phát triển, chuyên phát hiện và ẩn danh thông tin cá nhân (PII). Trong pipeline thực nghiệm, Presidio quét toàn bộ tài liệu trước khi chúng được embedding vào ChromaDB, tự động thay thế các trường nhạy cảm (tên, số CCCD, số thẻ) bằng các token đại diện. Thiết kế này đảm bảo bản thân Vector Database không bao giờ lưu trữ dữ liệu PII dạng rõ.

**Guardrails AI — LLM Output Redaction**
Guardrails AI được tích hợp làm lớp hậu kiểm cuối cùng, nằm giữa Agent và giao diện Chat. Bộ lọc này phân tích ngữ nghĩa và cú pháp của câu trả lời do LLM sinh ra, dò tìm các mẫu dữ liệu vi phạm chính sách bảo mật (như chuỗi số thẻ tín dụng, số CCCD còn sót). Nếu phát hiện vi phạm, Guardrails tự động bôi đen (redact) hoặc chặn đứng toàn bộ phản hồi.

**PostgreSQL — Cơ sở dữ liệu mô phỏng**
PostgreSQL được sử dụng thay thế Oracle Database trong môi trường lab. PostgreSQL hỗ trợ Row-Level Security (RLS) gốc thông qua cú pháp `CREATE POLICY`, cho phép mô phỏng chính xác cơ chế lọc dữ liệu cấp dòng mà OAS đang áp dụng tại SeABank. Khi nhận được truy vấn từ Agent, PostgreSQL sẽ kiểm tra biến `current_setting('app.user_branch')` (được truyền qua từ OBO Token) và tự động cắt tỉa kết quả theo đúng phạm vi chi nhánh.

**Docker Compose — Containerization & Sandboxing**
Toàn bộ 7 thành phần trên được đóng gói trong các container riêng biệt và triển khai thông qua Docker Compose. Mạng Docker nội bộ được cấu hình ở chế độ `internal: true`, chặn hoàn toàn luồng mạng xuất (egress) ra Internet. Agent sandbox chỉ được phép kết nối đến các container trong cùng mạng nội bộ (ChromaDB, PostgreSQL, Kong). Cấu hình này mô phỏng sát nhất cơ chế cô lập vùng mạng mà một hệ thống production tại ngân hàng yêu cầu.
