"""
Prompt templates cho Writer Agent.
"""

SQL_WRITER_GENERATION_PROMPT = """Nhiệm vụ: Viết câu lệnh SQL {db_dialect}.
Yêu cầu: {user_input}

Metadata (Schema và quan hệ JOIN từ Data Dictionary):
{metadata}

Hãy viết duy nhất câu lệnh SQL chuẩn xác, không có markdown block hay giải thích dư thừa.
Chỉ sử dụng bảng và cột có trong Metadata ở trên. TUYỆT ĐỐI KHÔNG tự bịa tên bảng hoặc cột.
Nếu cần JOIN nhiều bảng, ưu tiên các đường JOIN được mô tả trong Metadata.
Chỉ sinh một câu SELECT duy nhất.
Không thêm LIMIT, OFFSET hay FETCH FIRST — hệ thống sẽ giới hạn số dòng tự động.
"""

SQL_WRITER_REPAIR_PROMPT = """Nhiệm vụ: Sửa câu lệnh SQL {db_dialect} bị lỗi.
Yêu cầu gốc: {user_input}

Metadata (Schema và quan hệ JOIN từ Data Dictionary):
{metadata}

SQL trước đó:
{generated_sql}

Lỗi khi thực thi:
{execution_error}

Hãy sửa lại câu SQL để chạy được trên {db_dialect}.
Chỉ sử dụng bảng và cột có trong Metadata ở trên. TUYỆT ĐỐI KHÔNG tự bịa tên bảng hoặc cột.
Chỉ trả về duy nhất một câu SELECT, không markdown, không giải thích.
Không thêm LIMIT, OFFSET hay FETCH FIRST — hệ thống sẽ giới hạn số dòng tự động.
"""
