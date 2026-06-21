"""
========================================================================
OpenSearch Data Dictionary - General Ledger (GL) Banking Domain
========================================================================
Mô tả   : Khởi tạo kết nối OpenSearch, tạo index Data Dictionary,
           và nạp mock data nghiệp vụ Sổ Cái Ngân Hàng (GL).
Phiên bản: OpenSearch 3.6.0  |  Oracle DB backend
Tác giả  : Metadata Agent Setup Script
========================================================================
"""

import os
import time
from datetime import datetime

INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "data_dictionary")
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", 1024))


def _build_opensearch_config(requests_http_connection):
    return {
        "host": os.environ.get("OPENSEARCH_HOST", "localhost"),
        "port": int(os.environ.get("OPENSEARCH_PORT", 9200)),
        "use_ssl": True,
        "verify_certs": False,
        "http_auth": (
            os.environ.get("OPENSEARCH_USER", "admin"),
            os.environ.get("OPENSEARCH_PASSWORD", "MetadaaAgent@2026!"),
        ),
        "connection_class": requests_http_connection,
        "timeout": 30,
        "ssl_assert_hostname": False,
        "ssl_show_warn": False,
        "retry_on_timeout": True,
        "max_retries": 3,
    }


# ════════════════════════════════════════════════════════════
# 2. INDEX MAPPING (Schema cho Data Dictionary)
# ════════════════════════════════════════════════════════════

INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 2,
        "number_of_replicas": 1,
        "index.knn": True,
        "analysis": {
            "analyzer": {
                "vietnamese_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                }
            }
        },
    },
    "mappings": {
        "properties": {
            # ── Loại bản ghi ──────────────────────────────────────
            "record_type": {"type": "keyword"},  # TABLE | COLUMN | RELATIONSHIP
            # ── Phân loại nghiệp vụ ──────────────────────────────
            "domain_name": {"type": "keyword"},
            "system_source": {"type": "keyword"},
            "data_owner": {"type": "keyword"},
            "data_steward": {"type": "keyword"},
            "security_level": {"type": "keyword"},  # Public | Internal | Confidential
            # ── Định danh vật lý (Oracle) ─────────────────────────
            "database_name": {"type": "keyword"},
            "schema_name": {"type": "keyword"},
            "table_name": {"type": "keyword"},
            "column_name": {"type": "keyword"},
            "data_type": {"type": "keyword"},
            # ── Khoá & quan hệ ────────────────────────────────────
            "is_primary_key": {"type": "boolean"},
            "is_foreign_key": {"type": "boolean"},
            "references_table": {"type": "keyword"},
            "references_column": {"type": "keyword"},
            # ── Mô tả nghiệp vụ ──────────────────────────────────
            "business_name": {
                "type": "text",
                "analyzer": "vietnamese_analyzer",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "description": {"type": "text", "analyzer": "vietnamese_analyzer"},
            "calculation_logic": {"type": "text"},
            "allowed_values": {"type": "keyword"},
            "business_rules": {"type": "text", "analyzer": "vietnamese_analyzer"},
            # ── TABLE-level metadata ──────────────────────────────
            "table_purpose": {"type": "text", "analyzer": "vietnamese_analyzer"},
            "primary_key_columns": {"type": "keyword"},
            "natural_key": {"type": "keyword"},
            "related_tables": {"type": "keyword"},
            "estimated_row_count": {"type": "keyword"},
            # ── RELATIONSHIP-level metadata ───────────────────────
            "relationship_name": {
                "type": "text",
                "analyzer": "vietnamese_analyzer",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "join_path": {"type": "text"},
            "sample_sql": {"type": "text"},
            # ── Metadata quản trị ─────────────────────────────────
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
            "is_active": {"type": "boolean"},
            "version": {"type": "integer"},
            # ── Vector embedding (bge-m3 1024d) ─────────────────
            "description_vector": {
                "type": "knn_vector",
                "dimension": EMBEDDING_DIM,
                "method": {
                    "name": "hnsw",
                    "space_type": "innerproduct",
                    "engine": "faiss",
                    "parameters": {"ef_construction": 256, "m": 48},
                },
            },
        }
    },
}


# ════════════════════════════════════════════════════════════
# 3. MOCK DATA – NGHIỆP VỤ SỔ CÁI NGÂN HÀNG (GL)
#    Bao gồm 6 bảng Oracle chuẩn GL:
#      (1) GL_ACCOUNTS          – Danh mục tài khoản
#      (2) GL_JOURNAL_HEADERS   – Đầu bút toán
#      (3) GL_JOURNAL_LINES     – Chi tiết dòng bút toán
#      (4) GL_PERIODS           – Kỳ kế toán
#      (5) GL_COST_CENTERS      – Trung tâm chi phí
#      (6) GL_BALANCES          – Số dư tài khoản
# ════════════════════════════════════════════════════════════

NOW = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

COMMON = {
    "domain_name": "General Ledger",
    "system_source": "CORE_BANKING_SYSTEM",
    "data_owner": "Phòng Kế Toán Tổng Hợp",
    "data_steward": "Bộ Phận Quản Trị Dữ Liệu",
    "database_name": "COREDB",
    "created_at": NOW,
    "updated_at": NOW,
    "is_active": True,
    "version": 1,
}

COMMON_CIF = {
    "domain_name": "Customer Information",
    "system_source": "CORE_BANKING_SYSTEM",
    "data_owner": "Phòng Quản Lý Khách Hàng",
    "data_steward": "Bộ Phận Quản Trị Dữ Liệu",
    "database_name": "COREDB",
    "created_at": NOW,
    "updated_at": NOW,
    "is_active": True,
    "version": 1,
}


def record(
    schema,
    table,
    col,
    dtype,
    pk,
    fk,
    ref_tbl,
    ref_col,
    biz_name,
    desc,
    calc,
    allowed,
    rules,
    security="Confidential",
    common=None,
):
    """Tạo một document Data Dictionary (record_type=COLUMN)."""
    return {
        **(common or COMMON),
        "record_type": "COLUMN",
        "schema_name": schema,
        "table_name": table,
        "column_name": col,
        "data_type": dtype,
        "is_primary_key": pk,
        "is_foreign_key": fk,
        "references_table": ref_tbl,
        "references_column": ref_col,
        "business_name": biz_name,
        "description": desc,
        "calculation_logic": calc,
        "allowed_values": allowed,
        "business_rules": rules,
        "security_level": security,
    }


def table_record(
    schema,
    table,
    biz_name,
    desc,
    purpose,
    pk,
    natural_key,
    related,
    row_count,
    rules=None,
    security="Confidential",
    common=None,
):
    """Tạo một document mô tả tổng quan TABLE (record_type=TABLE)."""
    return {
        **(common or COMMON),
        "record_type": "TABLE",
        "schema_name": schema,
        "table_name": table,
        "business_name": biz_name,
        "description": desc,
        "table_purpose": purpose,
        "primary_key_columns": pk,
        "natural_key": natural_key,
        "related_tables": related,
        "estimated_row_count": row_count,
        "business_rules": rules,
        "security_level": security,
    }


def relationship_record(
    name,
    desc,
    join_path,
    sample_sql,
    tables,
    domain="Cross-Domain",
    common=None,
):
    """Tạo một document mô tả RELATIONSHIP / JOIN PATH (record_type=RELATIONSHIP)."""
    base = dict(common or COMMON)
    base["domain_name"] = domain
    return {
        **base,
        "record_type": "RELATIONSHIP",
        "relationship_name": name,
        "table_name": "_RELATIONSHIP",
        "description": desc,
        "join_path": join_path,
        "sample_sql": sample_sql,
        "related_tables": tables,
        "security_level": "Internal",
    }


# ────────────────────────────────────────────────────────────
# (1) GL_ACCOUNTS – Danh mục tài khoản kế toán
# ────────────────────────────────────────────────────────────
GL_ACCOUNTS = [
    record(
        "GL",
        "GL_ACCOUNTS",
        "ACCOUNT_ID",
        "NUMBER(10)",
        True,
        False,
        None,
        None,
        "Mã Tài Khoản",
        "Khóa chính định danh duy nhất mỗi tài khoản kế toán trong hệ thống sổ cái.",
        None,
        None,
        "Giá trị ACCOUNT_ID được sinh tự động bởi sequence GL_ACCOUNTS_SEQ. Không được phép sửa hoặc xóa sau khi đã có giao dịch tham chiếu.",
    ),
    record(
        "GL",
        "GL_ACCOUNTS",
        "ACCOUNT_CODE",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Số Tài Khoản",
        "Số tài khoản theo hệ thống tài khoản kế toán của Ngân hàng Nhà nước Việt Nam (TKVN).",
        None,
        [
            "1011: Tiền mặt tại quỹ VND",
            "1012: Tiền mặt tại quỹ ngoại tệ",
            "4211: Tiền gửi không kỳ hạn",
            "4231: Tiền gửi có kỳ hạn",
            "2111: Cho vay ngắn hạn",
            "2112: Cho vay trung dài hạn",
        ],
        "Mã tài khoản phải tuân thủ Quyết định 479/2004/QĐ-NHNN và các văn bản sửa đổi bổ sung. Độ dài từ 4–20 ký tự, chỉ chứa chữ số.",
    ),
    record(
        "GL",
        "GL_ACCOUNTS",
        "ACCOUNT_NAME",
        "NVARCHAR2(200)",
        False,
        False,
        None,
        None,
        "Tên Tài Khoản",
        "Tên đầy đủ của tài khoản kế toán bằng tiếng Việt, sử dụng trong báo cáo tài chính.",
        None,
        None,
        "Tên tài khoản phải khớp với danh mục chuẩn của NHNN. Không được để trống.",
    ),
    record(
        "GL",
        "GL_ACCOUNTS",
        "ACCOUNT_TYPE",
        "VARCHAR2(10)",
        False,
        False,
        None,
        None,
        "Loại Tài Khoản",
        "Phân loại tài khoản theo bản chất kế toán: tài sản, nợ phải trả, vốn chủ sở hữu, thu nhập, chi phí.",
        None,
        [
            "ASSET: Tài sản",
            "LIABILITY: Nợ phải trả",
            "EQUITY: Vốn chủ sở hữu",
            "REVENUE: Thu nhập",
            "EXPENSE: Chi phí",
        ],
        "Loại tài khoản xác định chiều ghi Nợ/Có mặc định. ASSET & EXPENSE: số dư Nợ bình thường; LIABILITY, EQUITY, REVENUE: số dư Có bình thường.",
    ),
    record(
        "GL",
        "GL_ACCOUNTS",
        "ACCOUNT_LEVEL",
        "NUMBER(2)",
        False,
        False,
        None,
        None,
        "Cấp Tài Khoản",
        "Cấp độ phân cấp của tài khoản trong cây tài khoản (cấp 1 = tài khoản tổng hợp, cấp 4 = tài khoản chi tiết).",
        None,
        [
            "1: Tài khoản cấp 1 (Loại)",
            "2: Tài khoản cấp 2 (Nhóm)",
            "3: Tài khoản cấp 3 (Tài khoản)",
            "4: Tài khoản cấp 4 (Chi tiết)",
        ],
        "Chỉ tài khoản cấp 4 (cấp thấp nhất) mới được phép có giao dịch phát sinh. Tài khoản cấp 1–3 chỉ dùng để tổng hợp báo cáo.",
    ),
    record(
        "GL",
        "GL_ACCOUNTS",
        "PARENT_ACCOUNT_ID",
        "NUMBER(10)",
        False,
        True,
        "GL_ACCOUNTS",
        "ACCOUNT_ID",
        "Mã Tài Khoản Cha",
        "Khóa ngoại trỏ đến tài khoản cha trong cấu trúc phân cấp. NULL nếu là tài khoản gốc cấp 1.",
        None,
        None,
        "Cây tài khoản không được tạo thành vòng lặp (circular reference). Tài khoản cấp 1 có PARENT_ACCOUNT_ID = NULL.",
    ),
    record(
        "GL",
        "GL_ACCOUNTS",
        "CURRENCY_CODE",
        "VARCHAR2(3)",
        False,
        False,
        None,
        None,
        "Mã Tiền Tệ",
        "Mã tiền tệ ISO 4217 của tài khoản. Tài khoản ngoại tệ lưu số dư theo nguyên tệ và VND quy đổi.",
        None,
        [
            "VND: Việt Nam Đồng",
            "USD: Đô la Mỹ",
            "EUR: Euro",
            "JPY: Yên Nhật",
            "CNY: Nhân dân tệ",
        ],
        "Tài khoản ngoại tệ bắt buộc ghi nhận thêm cột AMOUNT_VND theo tỷ giá hạch toán ngày giao dịch (Thông tư 200/2014/TT-BTC).",
    ),
    record(
        "GL",
        "GL_ACCOUNTS",
        "IS_CONTROL_ACCOUNT",
        "VARCHAR2(1)",
        False,
        False,
        None,
        None,
        "Tài Khoản Kiểm Soát",
        "Đánh dấu tài khoản là tài khoản kiểm soát (control account) – tổng hợp từ sổ phụ (sub-ledger).",
        None,
        ["Y: Là tài khoản kiểm soát", "N: Không phải tài khoản kiểm soát"],
        "Tài khoản kiểm soát (Y) không được ghi bút toán trực tiếp mà chỉ được cập nhật tự động từ module sub-ledger (AR, AP, FA).",
    ),
    record(
        "GL",
        "GL_ACCOUNTS",
        "STATUS",
        "VARCHAR2(10)",
        False,
        False,
        None,
        None,
        "Trạng Thái Tài Khoản",
        "Trạng thái hoạt động của tài khoản trong hệ thống.",
        None,
        ["ACTIVE: Đang hoạt động", "INACTIVE: Ngừng sử dụng", "CLOSED: Đã đóng"],
        "Tài khoản INACTIVE không được tạo giao dịch mới nhưng vẫn hiển thị số dư lịch sử. Tài khoản CLOSED phải có số dư = 0.",
    ),
    record(
        "GL",
        "GL_ACCOUNTS",
        "EFFECTIVE_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Hiệu Lực",
        "Ngày tài khoản bắt đầu được phép sử dụng trong hệ thống kế toán.",
        None,
        None,
        "EFFECTIVE_DATE <= ngày giao dịch <= END_DATE. Không được tạo bút toán trước EFFECTIVE_DATE.",
    ),
    record(
        "GL",
        "GL_ACCOUNTS",
        "END_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Hết Hiệu Lực",
        "Ngày cuối cùng tài khoản được phép nhận giao dịch. NULL nghĩa là tài khoản không có ngày hết hạn.",
        None,
        None,
        "Khi END_DATE < SYSDATE, hệ thống tự động chuyển STATUS sang INACTIVE. Giá trị NULL cho phép giao dịch vô thời hạn.",
    ),
]

# ────────────────────────────────────────────────────────────
# (2) GL_PERIODS – Kỳ kế toán
# ────────────────────────────────────────────────────────────
GL_PERIODS = [
    record(
        "GL",
        "GL_PERIODS",
        "PERIOD_ID",
        "NUMBER(10)",
        True,
        False,
        None,
        None,
        "Mã Kỳ Kế Toán",
        "Khóa chính định danh duy nhất kỳ kế toán.",
        None,
        None,
        "Sinh tự động bởi GL_PERIODS_SEQ.",
    ),
    record(
        "GL",
        "GL_PERIODS",
        "PERIOD_NAME",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Tên Kỳ Kế Toán",
        "Tên kỳ kế toán theo định dạng YYYY-MM (VD: 2024-01 là tháng 1 năm 2024).",
        None,
        None,
        "Định dạng bắt buộc: YYYY-MM. Dùng làm khóa logic tra cứu trong báo cáo tài chính tháng.",
    ),
    record(
        "GL",
        "GL_PERIODS",
        "FISCAL_YEAR",
        "NUMBER(4)",
        False,
        False,
        None,
        None,
        "Năm Tài Chính",
        "Năm tài chính (fiscal year) mà kỳ kế toán thuộc về. Năm tài chính của ngân hàng trùng với năm dương lịch (1/1 – 31/12).",
        None,
        None,
        "FISCAL_YEAR phải khớp với 4 chữ số đầu của PERIOD_NAME. Kiểm soát bởi trigger GL_PERIODS_BIU.",
    ),
    record(
        "GL",
        "GL_PERIODS",
        "PERIOD_NUMBER",
        "NUMBER(2)",
        False,
        False,
        None,
        None,
        "Số Thứ Tự Kỳ",
        "Số thứ tự của kỳ kế toán trong năm tài chính (1–12 cho kỳ thường, 13 = kỳ điều chỉnh cuối năm).",
        None,
        ["1–12: Tháng 1 đến tháng 12", "13: Kỳ điều chỉnh (Adjustment Period)"],
        "Kỳ 13 chỉ dùng để ghi các bút toán điều chỉnh sau kiểm toán. Không có giao dịch phát sinh thông thường trong kỳ 13.",
    ),
    record(
        "GL",
        "GL_PERIODS",
        "START_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Bắt Đầu Kỳ",
        "Ngày đầu tiên của kỳ kế toán (thường là ngày 01 của tháng).",
        None,
        None,
        "START_DATE phải là ngày đầu tiên trong tháng. Bút toán có ngày giao dịch trong [START_DATE, END_DATE] được hạch toán vào kỳ này.",
    ),
    record(
        "GL",
        "GL_PERIODS",
        "END_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Kết Thúc Kỳ",
        "Ngày cuối cùng của kỳ kế toán (thường là ngày cuối tháng).",
        None,
        None,
        "END_DATE luôn là ngày cuối cùng trong tháng dương lịch. END_DATE >= START_DATE.",
    ),
    record(
        "GL",
        "GL_PERIODS",
        "STATUS",
        "VARCHAR2(10)",
        False,
        False,
        None,
        None,
        "Trạng Thái Kỳ Kế Toán",
        "Trạng thái đóng/mở của kỳ kế toán, quyết định khả năng nhận bút toán mới.",
        None,
        [
            "OPEN: Đang mở – nhận bút toán mới",
            "CLOSED: Đã đóng – không nhận bút toán mới",
            "FUTURE: Kỳ tương lai – chưa mở",
            "NEVER_OPENED: Chưa bao giờ mở",
        ],
        "Chỉ kỳ có STATUS='OPEN' mới cho phép tạo bút toán. Đóng kỳ (CLOSED) là thao tác không thể hoàn tác. Cần phê duyệt của Kế toán trưởng.",
    ),
    record(
        "GL",
        "GL_PERIODS",
        "CLOSING_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Chốt Sổ",
        "Ngày thực tế thực hiện chốt sổ kỳ kế toán. NULL nếu kỳ chưa được chốt.",
        None,
        None,
        "CLOSING_DATE được ghi nhận tự động khi Kế toán trưởng thực hiện thao tác Close Period. Không cho phép sửa thủ công.",
    ),
]

# ────────────────────────────────────────────────────────────
# (3) GL_COST_CENTERS – Trung tâm chi phí / Đơn vị kinh doanh
# ────────────────────────────────────────────────────────────
GL_COST_CENTERS = [
    record(
        "GL",
        "GL_COST_CENTERS",
        "COST_CENTER_ID",
        "NUMBER(10)",
        True,
        False,
        None,
        None,
        "Mã Trung Tâm Chi Phí",
        "Khóa chính định danh duy nhất trung tâm chi phí.",
        None,
        None,
        "Sinh tự động bởi GL_COST_CENTERS_SEQ.",
    ),
    record(
        "GL",
        "GL_COST_CENTERS",
        "COST_CENTER_CODE",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Số Hiệu TTCP",
        "Mã số hiệu trung tâm chi phí theo cơ cấu tổ chức nội bộ ngân hàng.",
        None,
        [
            "HO: Hội sở chính",
            "CN-HN-001: Chi nhánh Hà Nội 001",
            "CN-HCM-001: Chi nhánh HCM 001",
            "PGD-HN-001: Phòng giao dịch HN 001",
            "TT-IT: Trung tâm CNTT",
            "TT-RM: Trung tâm Quản lý Rủi ro",
        ],
        "Mã TTCP phải duy nhất trong toàn hệ thống. Cấu trúc mã theo phân cấp: HO > CN > PGD.",
    ),
    record(
        "GL",
        "GL_COST_CENTERS",
        "COST_CENTER_NAME",
        "NVARCHAR2(200)",
        False,
        False,
        None,
        None,
        "Tên Trung Tâm Chi Phí",
        "Tên đầy đủ của trung tâm chi phí bằng tiếng Việt.",
        None,
        None,
        "Tên phải khớp với cơ cấu tổ chức được phê duyệt bởi Hội đồng quản trị. Cập nhật khi có thay đổi tổ chức.",
    ),
    record(
        "GL",
        "GL_COST_CENTERS",
        "COST_CENTER_TYPE",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Loại Trung Tâm Chi Phí",
        "Phân loại trung tâm chi phí theo chức năng kinh doanh.",
        None,
        [
            "HEAD_OFFICE: Hội sở",
            "BRANCH: Chi nhánh",
            "SUB_BRANCH: Phòng giao dịch",
            "SUPPORT: Đơn vị hỗ trợ",
            "PROFIT_CENTER: Trung tâm lợi nhuận",
        ],
        "Phân loại này ảnh hưởng đến phương pháp phân bổ chi phí và lập báo cáo P&L theo đơn vị.",
    ),
    record(
        "GL",
        "GL_COST_CENTERS",
        "REGION_CODE",
        "VARCHAR2(10)",
        False,
        False,
        None,
        None,
        "Mã Vùng",
        "Mã vùng địa lý mà trung tâm chi phí trực thuộc, phục vụ phân tích theo khu vực.",
        None,
        ["NORTH: Miền Bắc", "CENTRAL: Miền Trung", "SOUTH: Miền Nam", "HO: Hội sở"],
        "Báo cáo doanh thu và chi phí theo vùng dựa trên REGION_CODE của TTCP phát sinh giao dịch.",
    ),
    record(
        "GL",
        "GL_COST_CENTERS",
        "MANAGER_EMP_ID",
        "NUMBER(10)",
        False,
        False,
        None,
        None,
        "Mã Nhân Viên Phụ Trách",
        "Mã nhân viên của người phụ trách (Giám đốc/Trưởng đơn vị) trung tâm chi phí.",
        None,
        None,
        "Dùng để phân quyền duyệt bút toán và xem báo cáo chi phí. Phải là nhân viên đang hoạt động trong hệ thống HR.",
    ),
    record(
        "GL",
        "GL_COST_CENTERS",
        "STATUS",
        "VARCHAR2(10)",
        False,
        False,
        None,
        None,
        "Trạng Thái",
        "Trạng thái hoạt động của trung tâm chi phí.",
        None,
        ["ACTIVE: Đang hoạt động", "INACTIVE: Ngừng hoạt động", "MERGED: Đã sáp nhập"],
        "TTCP INACTIVE không được ghi nhận giao dịch mới. TTCP MERGED phải có trường MERGED_INTO_ID trỏ đến TTCP kế thừa.",
    ),
]

# ────────────────────────────────────────────────────────────
# (4) GL_JOURNAL_HEADERS – Đầu bút toán kế toán
# ────────────────────────────────────────────────────────────
GL_JOURNAL_HEADERS = [
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "JOURNAL_ID",
        "NUMBER(15)",
        True,
        False,
        None,
        None,
        "Mã Bút Toán",
        "Khóa chính định danh duy nhất một bút toán kế toán (journal entry) trong hệ thống GL.",
        None,
        None,
        "Sinh tự động bởi GL_JOURNAL_SEQ. Là số tham chiếu duy nhất cho toàn bộ vòng đời bút toán.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "JOURNAL_NUMBER",
        "VARCHAR2(30)",
        False,
        False,
        None,
        None,
        "Số Chứng Từ",
        "Số chứng từ kế toán hiển thị cho người dùng, theo định dạng [PREFIX]-[YYYY]-[NNNNNN].",
        "Ghép chuỗi: PREFIX || '-' || TO_CHAR(JOURNAL_DATE,'YYYY') || '-' || LPAD(SEQ,6,'0')",
        [
            "JV: Bút toán thủ công",
            "AC: Bút toán tự động",
            "RE: Bút toán đảo ngược",
            "CL: Bút toán kết chuyển cuối kỳ",
        ],
        "JOURNAL_NUMBER phải duy nhất trong năm tài chính. Số chứng từ không được thay đổi sau khi bút toán được duyệt.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "JOURNAL_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Hạch Toán",
        "Ngày giao dịch kế toán, xác định kỳ kế toán mà bút toán được ghi nhận.",
        None,
        None,
        "JOURNAL_DATE phải thuộc kỳ kế toán đang OPEN. Không được hạch toán vào kỳ đã CLOSED. Ngày hạch toán không nhất thiết trùng ngày tạo (CREATION_DATE).",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "ACCOUNTING_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Kế Toán",
        "Ngày ghi nhận kế toán chính thức (có thể khác ngày hạch toán trong trường hợp điều chỉnh).",
        None,
        None,
        "ACCOUNTING_DATE = JOURNAL_DATE trong hầu hết trường hợp. Chỉ khác nhau với bút toán điều chỉnh hồi tố (prior period adjustment) được phê duyệt bởi CFO.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "PERIOD_ID",
        "NUMBER(10)",
        False,
        True,
        "GL_PERIODS",
        "PERIOD_ID",
        "Mã Kỳ Kế Toán",
        "Khóa ngoại trỏ đến kỳ kế toán mà bút toán này thuộc về.",
        None,
        None,
        "Được gán tự động dựa trên JOURNAL_DATE. Kỳ phải có STATUS='OPEN'. Không thể thay đổi sau khi bút toán đã POSTED.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "JOURNAL_TYPE",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Loại Bút Toán",
        "Phân loại bút toán theo nguồn gốc và tính chất giao dịch.",
        None,
        [
            "MANUAL: Bút toán thủ công",
            "AUTO_ACCRUAL: Dự thu tự động",
            "AUTO_REVERSAL: Đảo ngược tự động",
            "ALLOCATION: Phân bổ chi phí",
            "CLOSING: Kết chuyển cuối kỳ",
            "OPENING: Bút toán đầu kỳ",
            "INTERCOMPANY: Nội bộ liên đơn vị",
            "REVALUATION: Đánh giá lại ngoại tệ",
        ],
        "Loại bút toán quyết định luồng phê duyệt. MANUAL yêu cầu ít nhất 1 cấp duyệt. CLOSING/OPENING chỉ do hệ thống tạo.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "DESCRIPTION",
        "NVARCHAR2(500)",
        False,
        False,
        None,
        None,
        "Diễn Giải Bút Toán",
        "Mô tả nội dung kinh tế của bút toán, làm căn cứ cho kiểm toán và tra cứu.",
        None,
        None,
        "Bắt buộc nhập với bút toán MANUAL. Tối thiểu 10 ký tự. Không được chứa thông tin bí mật khách hàng.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "REFERENCE_NUMBER",
        "VARCHAR2(100)",
        False,
        False,
        None,
        None,
        "Số Tham Chiếu Nguồn",
        "Số chứng từ gốc từ hệ thống nghiệp vụ phát sinh bút toán (VD: số hợp đồng, số lệnh chuyển tiền).",
        None,
        None,
        "Dùng để đối chiếu ngược từ GL về hệ thống nghiệp vụ gốc. Bắt buộc với bút toán AUTO từ sub-ledger.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "SOURCE_SYSTEM",
        "VARCHAR2(50)",
        False,
        False,
        None,
        None,
        "Hệ Thống Nguồn",
        "Tên hệ thống nghiệp vụ tạo ra bút toán kế toán này.",
        None,
        [
            "GL_MANUAL: Nhập tay trên GL",
            "LOAN_SYSTEM: Hệ thống tín dụng",
            "DEPOSIT_SYSTEM: Hệ thống huy động vốn",
            "TREASURY: Hệ thống nguồn vốn",
            "CARD_SYSTEM: Hệ thống thẻ",
            "TRADE_FINANCE: Tài trợ thương mại",
            "PAYROLL: Hệ thống nhân sự lương",
            "FIXED_ASSET: Tài sản cố định",
        ],
        "SOURCE_SYSTEM kết hợp với REFERENCE_NUMBER tạo thành khóa đối chiếu duy nhất với hệ thống gốc.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "STATUS",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Trạng Thái Bút Toán",
        "Trạng thái xử lý của bút toán trong quy trình phê duyệt và hạch toán.",
        None,
        [
            "DRAFT: Nháp – đang soạn thảo",
            "PENDING_APPROVAL: Chờ phê duyệt",
            "APPROVED: Đã phê duyệt",
            "POSTED: Đã hạch toán vào sổ cái",
            "REVERSED: Đã bị đảo ngược",
            "CANCELLED: Đã hủy",
        ],
        "Chỉ bút toán POSTED mới ảnh hưởng đến số dư tài khoản (GL_BALANCES). Không được phép xóa bút toán đã POSTED; phải tạo bút toán đảo ngược (REVERSED).",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "TOTAL_DEBIT",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Tổng Phát Sinh Nợ",
        "Tổng số tiền ghi Nợ của toàn bộ dòng bút toán trong chứng từ này (đơn vị: VND).",
        "SUM(LINE.DEBIT_AMOUNT) WHERE JOURNAL_ID = HEADER.JOURNAL_ID",
        None,
        "TOTAL_DEBIT phải bằng TOTAL_CREDIT (nguyên tắc bút toán kép). Hệ thống từ chối POSTED nếu TOTAL_DEBIT <> TOTAL_CREDIT.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "TOTAL_CREDIT",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Tổng Phát Sinh Có",
        "Tổng số tiền ghi Có của toàn bộ dòng bút toán trong chứng từ này (đơn vị: VND).",
        "SUM(LINE.CREDIT_AMOUNT) WHERE JOURNAL_ID = HEADER.JOURNAL_ID",
        None,
        "TOTAL_CREDIT phải bằng TOTAL_DEBIT. Sai lệch ngay cả 1 đồng sẽ khiến bút toán không thể hạch toán.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "REVERSAL_FLAG",
        "VARCHAR2(1)",
        False,
        False,
        None,
        None,
        "Cờ Đảo Ngược",
        "Đánh dấu bút toán có được thiết lập tự động đảo ngược vào kỳ tiếp theo hay không.",
        None,
        ["Y: Tự động đảo ngược", "N: Không đảo ngược"],
        "Dùng cho bút toán dự thu dự chi (accrual). Khi kỳ mới mở, hệ thống tự tạo bút toán đảo ngược với JOURNAL_TYPE = AUTO_REVERSAL.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "REVERSAL_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Đảo Ngược",
        "Ngày dự kiến thực hiện đảo ngược bút toán. Chỉ có giá trị khi REVERSAL_FLAG = 'Y'.",
        None,
        None,
        "REVERSAL_DATE phải thuộc kỳ kế toán tương lai (> JOURNAL_DATE). Thường là ngày đầu tiên của tháng tiếp theo.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "CREATED_BY",
        "VARCHAR2(50)",
        False,
        False,
        None,
        None,
        "Người Tạo",
        "Tên đăng nhập (username) của người dùng tạo bút toán.",
        None,
        None,
        "Ghi nhận tự động từ session người dùng. Không cho phép sửa thủ công. Dùng cho audit trail.",
    ),
    record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "APPROVED_BY",
        "VARCHAR2(50)",
        False,
        False,
        None,
        None,
        "Người Phê Duyệt",
        "Tên đăng nhập của người phê duyệt bút toán. NULL nếu chưa phê duyệt.",
        None,
        None,
        "APPROVED_BY không được trùng CREATED_BY (nguyên tắc tách biệt nhiệm vụ - segregation of duties). Kiểm soát bởi trigger GL_JOURNAL_APPROVAL_CHECK.",
    ),
]

# ────────────────────────────────────────────────────────────
# (5) GL_JOURNAL_LINES – Chi tiết dòng bút toán
# ────────────────────────────────────────────────────────────
GL_JOURNAL_LINES = [
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "LINE_ID",
        "NUMBER(15)",
        True,
        False,
        None,
        None,
        "Mã Dòng Bút Toán",
        "Khóa chính định danh duy nhất một dòng trong bút toán kế toán.",
        None,
        None,
        "Sinh tự động bởi GL_JOURNAL_LINES_SEQ.",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "JOURNAL_ID",
        "NUMBER(15)",
        False,
        True,
        "GL_JOURNAL_HEADERS",
        "JOURNAL_ID",
        "Mã Bút Toán",
        "Khóa ngoại trỏ đến bút toán (header) mà dòng này thuộc về.",
        None,
        None,
        "Bắt buộc. Khi xóa HEADER (trạng thái DRAFT), toàn bộ LINES liên quan bị xóa theo (CASCADE DELETE).",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "LINE_NUMBER",
        "NUMBER(5)",
        False,
        False,
        None,
        None,
        "Số Thứ Tự Dòng",
        "Số thứ tự của dòng trong bút toán, bắt đầu từ 1.",
        None,
        None,
        "LINE_NUMBER duy nhất trong phạm vi JOURNAL_ID. Tự tăng theo thứ tự thêm dòng.",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "ACCOUNT_ID",
        "NUMBER(10)",
        False,
        True,
        "GL_ACCOUNTS",
        "ACCOUNT_ID",
        "Mã Tài Khoản",
        "Khóa ngoại trỏ đến tài khoản kế toán được ghi nợ hoặc ghi có trong dòng này.",
        None,
        None,
        "Chỉ được phép dùng tài khoản cấp 4 (ACCOUNT_LEVEL=4) và STATUS='ACTIVE'. Tài khoản kiểm soát (IS_CONTROL_ACCOUNT='Y') không được dùng trực tiếp.",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "COST_CENTER_ID",
        "NUMBER(10)",
        False,
        True,
        "GL_COST_CENTERS",
        "COST_CENTER_ID",
        "Mã Trung Tâm Chi Phí",
        "Khóa ngoại trỏ đến trung tâm chi phí/đơn vị kinh doanh phát sinh giao dịch.",
        None,
        None,
        "Bắt buộc cho tài khoản chi phí và thu nhập (ACCOUNT_TYPE IN ('EXPENSE','REVENUE')). Tùy chọn cho tài khoản tài sản và nợ phải trả.",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "DEBIT_AMOUNT",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Số Tiền Nợ",
        "Số tiền ghi Nợ của dòng bút toán này (đơn vị: VND). 0 nếu dòng ghi Có.",
        None,
        None,
        "DEBIT_AMOUNT >= 0. Chỉ một trong hai DEBIT_AMOUNT và CREDIT_AMOUNT được > 0 trong cùng một dòng. Không cho phép cả hai đều > 0.",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "CREDIT_AMOUNT",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Số Tiền Có",
        "Số tiền ghi Có của dòng bút toán này (đơn vị: VND). 0 nếu dòng ghi Nợ.",
        None,
        None,
        "CREDIT_AMOUNT >= 0. DEBIT_AMOUNT + CREDIT_AMOUNT > 0 (ít nhất một giá trị phải dương). CHECK constraint: NOT (DEBIT_AMOUNT > 0 AND CREDIT_AMOUNT > 0).",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "CURRENCY_CODE",
        "VARCHAR2(3)",
        False,
        False,
        None,
        None,
        "Mã Nguyên Tệ",
        "Mã tiền tệ gốc của giao dịch theo ISO 4217. Có thể khác VND đối với giao dịch ngoại tệ.",
        None,
        ["VND", "USD", "EUR", "JPY", "CNY", "GBP", "AUD", "SGD"],
        "Khi CURRENCY_CODE <> 'VND', bắt buộc phải có EXCHANGE_RATE và AMOUNT_ORIGINAL. DEBIT/CREDIT_AMOUNT luôn lưu giá trị VND quy đổi.",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "AMOUNT_ORIGINAL",
        "NUMBER(20,4)",
        False,
        False,
        None,
        None,
        "Số Tiền Nguyên Tệ",
        "Số tiền theo nguyên tệ của giao dịch trước khi quy đổi sang VND.",
        None,
        None,
        "Bắt buộc khi CURRENCY_CODE <> 'VND'. AMOUNT_ORIGINAL * EXCHANGE_RATE = DEBIT_AMOUNT hoặc CREDIT_AMOUNT (sai lệch <= 1 VND do làm tròn).",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "EXCHANGE_RATE",
        "NUMBER(15,6)",
        False,
        False,
        None,
        None,
        "Tỷ Giá Hạch Toán",
        "Tỷ giá quy đổi nguyên tệ sang VND tại ngày hạch toán (số VND trên 1 đơn vị nguyên tệ).",
        None,
        None,
        "Tỷ giá sử dụng là tỷ giá hạch toán của NHNN công bố tại ngày JOURNAL_DATE, hoặc tỷ giá mua/bán tùy loại giao dịch theo Thông tư 200.",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "LINE_DESCRIPTION",
        "NVARCHAR2(500)",
        False,
        False,
        None,
        None,
        "Diễn Giải Dòng",
        "Mô tả nội dung cụ thể của dòng bút toán, chi tiết hơn diễn giải ở cấp header.",
        None,
        None,
        "Nếu không nhập, hệ thống kế thừa từ DESCRIPTION của GL_JOURNAL_HEADERS. Với bút toán AUTO, LINE_DESCRIPTION được sinh tự động từ template.",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "TAX_CODE",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Mã Thuế",
        "Mã loại thuế áp dụng cho giao dịch này (VAT, PITAX...). NULL nếu không liên quan đến thuế.",
        None,
        [
            "VAT10: VAT 10%",
            "VAT8: VAT 8% (theo NQ)",
            "VAT0: VAT 0% hàng xuất khẩu",
            "VATEX: Miễn thuế VAT",
            "PITAX: Thuế thu nhập cá nhân",
        ],
        "TAX_CODE bắt buộc với giao dịch dịch vụ chịu thuế. Tích hợp với module Tax để tự động tính và khai báo thuế.",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "RECONCILIATION_STATUS",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Trạng Thái Đối Chiếu",
        "Trạng thái đối chiếu của dòng bút toán với sao kê ngân hàng hoặc hệ thống đối tác.",
        None,
        [
            "UNRECONCILED: Chưa đối chiếu",
            "RECONCILED: Đã đối chiếu",
            "PARTIALLY_RECONCILED: Đối chiếu một phần",
            "EXCEPTION: Có sai lệch cần xử lý",
        ],
        "Bước đối chiếu (reconciliation) là kiểm soát nội bộ bắt buộc hàng tháng. Dòng EXCEPTION phải được giải trình trong 3 ngày làm việc.",
    ),
    record(
        "GL",
        "GL_JOURNAL_LINES",
        "CUSTOMER_ID",
        "NUMBER(15)",
        False,
        True,
        "CIF_CUSTOMERS",
        "CUSTOMER_ID",
        "Mã Khách Hàng",
        "Khóa ngoại trỏ đến khách hàng liên quan đến giao dịch. NULL nếu giao dịch không gắn trực tiếp với khách hàng cụ thể (VD: bút toán phân bổ nội bộ).",
        None,
        None,
        "Bắt buộc với giao dịch phát sinh từ nghiệp vụ khách hàng (LOAN_SYSTEM, DEPOSIT_SYSTEM, CARD_SYSTEM). Tùy chọn với bút toán nội bộ. Dùng để tra soát và đối chiếu giao dịch theo hồ sơ khách hàng.",
    ),
]

# ────────────────────────────────────────────────────────────
# (6) GL_BALANCES – Số dư tài khoản theo kỳ kế toán
# ────────────────────────────────────────────────────────────
GL_BALANCES = [
    record(
        "GL",
        "GL_BALANCES",
        "BALANCE_ID",
        "NUMBER(15)",
        True,
        False,
        None,
        None,
        "Mã Số Dư",
        "Khóa chính định danh duy nhất một bản ghi số dư.",
        None,
        None,
        "Sinh tự động bởi GL_BALANCES_SEQ.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "ACCOUNT_ID",
        "NUMBER(10)",
        False,
        True,
        "GL_ACCOUNTS",
        "ACCOUNT_ID",
        "Mã Tài Khoản",
        "Khóa ngoại trỏ đến tài khoản kế toán của bản ghi số dư này.",
        None,
        None,
        "Kết hợp (ACCOUNT_ID, COST_CENTER_ID, PERIOD_ID, CURRENCY_CODE) tạo thành khóa tự nhiên duy nhất của GL_BALANCES.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "COST_CENTER_ID",
        "NUMBER(10)",
        False,
        True,
        "GL_COST_CENTERS",
        "COST_CENTER_ID",
        "Mã Trung Tâm Chi Phí",
        "Khóa ngoại trỏ đến trung tâm chi phí của bản ghi số dư.",
        None,
        None,
        "Số dư được lưu chi tiết đến từng cặp (Tài khoản, TTCP) để hỗ trợ báo cáo P&L theo đơn vị kinh doanh.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "PERIOD_ID",
        "NUMBER(10)",
        False,
        True,
        "GL_PERIODS",
        "PERIOD_ID",
        "Mã Kỳ Kế Toán",
        "Khóa ngoại trỏ đến kỳ kế toán của bản ghi số dư.",
        None,
        None,
        "Mỗi kỳ kế toán sẽ có một bản ghi GL_BALANCES tương ứng cho mỗi tổ hợp (tài khoản, TTCP, tiền tệ). Được tạo/cập nhật khi POSTING bút toán.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "CURRENCY_CODE",
        "VARCHAR2(3)",
        False,
        False,
        None,
        None,
        "Mã Tiền Tệ",
        "Mã tiền tệ của số dư: 'VND' cho số dư VND, hoặc mã ngoại tệ cho số dư ngoại tệ.",
        None,
        ["VND", "USD", "EUR", "JPY", "CNY"],
        "Với tài khoản ngoại tệ, lưu 2 dòng: 1 dòng nguyên tệ và 1 dòng VND quy đổi. Báo cáo tài chính hợp nhất chỉ dùng dòng VND.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "OPENING_BALANCE_DR",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Số Dư Đầu Kỳ Nợ",
        "Số dư Nợ đầu kỳ của tài khoản tại thời điểm bắt đầu kỳ kế toán (đơn vị: VND).",
        "GL_BALANCES(kỳ trước).CLOSING_BALANCE_DR",
        None,
        "OPENING_BALANCE = CLOSING_BALANCE của kỳ liền trước. Được sao chép tự động khi mở kỳ mới (Open Period).",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "OPENING_BALANCE_CR",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Số Dư Đầu Kỳ Có",
        "Số dư Có đầu kỳ của tài khoản tại thời điểm bắt đầu kỳ kế toán (đơn vị: VND).",
        "GL_BALANCES(kỳ trước).CLOSING_BALANCE_CR",
        None,
        "Tương tự OPENING_BALANCE_DR nhưng cho số dư Có. Một tài khoản tại một thời điểm chỉ có số dư ở một phía (Nợ hoặc Có).",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "PERIOD_ACTIVITY_DR",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Phát Sinh Nợ Trong Kỳ",
        "Tổng số tiền phát sinh Nợ trong kỳ kế toán từ tất cả bút toán đã POSTED.",
        "SUM(GL_JOURNAL_LINES.DEBIT_AMOUNT) WHERE PERIOD_ID = kỳ hiện tại AND ACCOUNT_ID = tài khoản hiện tại",
        None,
        "Cập nhật tức thời mỗi khi có bút toán POSTED vào kỳ. Được tái tính lại (recalculate) khi có bút toán đảo ngược.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "PERIOD_ACTIVITY_CR",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Phát Sinh Có Trong Kỳ",
        "Tổng số tiền phát sinh Có trong kỳ kế toán từ tất cả bút toán đã POSTED.",
        "SUM(GL_JOURNAL_LINES.CREDIT_AMOUNT) WHERE PERIOD_ID = kỳ hiện tại AND ACCOUNT_ID = tài khoản hiện tại",
        None,
        "Tương tự PERIOD_ACTIVITY_DR nhưng tổng hợp phát sinh Có.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "CLOSING_BALANCE_DR",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Số Dư Cuối Kỳ Nợ",
        "Số dư Nợ cuối kỳ sau khi cộng/trừ toàn bộ phát sinh trong kỳ.",
        "OPENING_BALANCE_DR + PERIOD_ACTIVITY_DR - PERIOD_ACTIVITY_CR (nếu kết quả > 0)",
        None,
        "CLOSING_BALANCE_DR và CLOSING_BALANCE_CR không thể cùng > 0 cho một tài khoản tại cùng kỳ. Kiểm soát bởi constraint CHECK.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "CLOSING_BALANCE_CR",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Số Dư Cuối Kỳ Có",
        "Số dư Có cuối kỳ sau khi cộng/trừ toàn bộ phát sinh trong kỳ.",
        "OPENING_BALANCE_CR + PERIOD_ACTIVITY_CR - PERIOD_ACTIVITY_DR (nếu kết quả > 0)",
        None,
        "Tương tự CLOSING_BALANCE_DR. Dùng để lập Bảng cân đối kế toán (Balance Sheet) và Bảng cân đối tài khoản.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "YTD_ACTIVITY_DR",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Lũy Kế Phát Sinh Nợ Từ Đầu Năm",
        "Tổng phát sinh Nợ lũy kế từ đầu năm tài chính đến hết kỳ hiện tại.",
        "SUM(PERIOD_ACTIVITY_DR) WHERE FISCAL_YEAR = năm hiện tại AND PERIOD_NUMBER <= kỳ hiện tại",
        None,
        "YTD (Year-To-Date) dùng cho Báo cáo kết quả kinh doanh lũy kế. Reset về 0 đầu mỗi năm tài chính.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "YTD_ACTIVITY_CR",
        "NUMBER(20,2)",
        False,
        False,
        None,
        None,
        "Lũy Kế Phát Sinh Có Từ Đầu Năm",
        "Tổng phát sinh Có lũy kế từ đầu năm tài chính đến hết kỳ hiện tại.",
        "SUM(PERIOD_ACTIVITY_CR) WHERE FISCAL_YEAR = năm hiện tại AND PERIOD_NUMBER <= kỳ hiện tại",
        None,
        "Tương tự YTD_ACTIVITY_DR. Kết hợp YTD_DR và YTD_CR để tính lợi nhuận/lỗ lũy kế.",
    ),
    record(
        "GL",
        "GL_BALANCES",
        "LAST_UPDATED",
        "TIMESTAMP(6)",
        False,
        False,
        None,
        None,
        "Thời Điểm Cập Nhật Cuối",
        "Timestamp chính xác đến microsecond ghi nhận lần cập nhật cuối cùng của bản ghi số dư.",
        None,
        None,
        "Cập nhật tự động bởi trigger GL_BALANCES_AUD. Dùng để phát hiện số dư bị thay đổi bất thường và hỗ trợ đồng bộ data warehouse.",
    ),
]


# ────────────────────────────────────────────────────────────
# (7) CIF_CUSTOMERS – Thông tin khách hàng
# ────────────────────────────────────────────────────────────
CIF_CUSTOMERS = [
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "CUSTOMER_ID",
        "NUMBER(15)",
        True,
        False,
        None,
        None,
        "Mã Khách Hàng",
        "Khóa chính định danh duy nhất khách hàng trong hệ thống Core Banking.",
        None,
        None,
        "Sinh tự động bởi CIF_CUSTOMERS_SEQ. Là mã nội bộ hệ thống, không hiển thị cho khách hàng.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "CIF_NUMBER",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Số CIF",
        "Số CIF (Customer Information File) – mã định danh khách hàng duy nhất hiển thị trên giao diện và chứng từ.",
        None,
        ["CIF + 10 chữ số, VD: CIF0000000001"],
        "CIF_NUMBER phải duy nhất toàn hệ thống. Định dạng: 'CIF' + 10 chữ số. Không được thay đổi sau khi cấp.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "CUSTOMER_TYPE",
        "VARCHAR2(15)",
        False,
        False,
        None,
        None,
        "Loại Khách Hàng",
        "Phân loại khách hàng theo tính chất pháp lý: cá nhân hoặc tổ chức/doanh nghiệp.",
        None,
        [
            "INDIVIDUAL: Khách hàng cá nhân",
            "CORPORATE: Khách hàng doanh nghiệp/tổ chức",
        ],
        "Loại khách hàng quyết định bộ hồ sơ pháp lý yêu cầu (KYC) và hạn mức giao dịch áp dụng.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "FULL_NAME",
        "NVARCHAR2(200)",
        False,
        False,
        None,
        None,
        "Họ Tên Đầy Đủ",
        "Họ tên đầy đủ của khách hàng cá nhân hoặc tên đăng ký kinh doanh của khách hàng doanh nghiệp.",
        None,
        None,
        "Phải khớp với giấy tờ tùy thân (CMND/CCCD) hoặc Giấy CNĐKKD. Không được viết tắt. Lưu bằng chữ in hoa có dấu.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "DATE_OF_BIRTH",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Sinh / Ngày Thành Lập",
        "Ngày sinh của khách hàng cá nhân hoặc ngày thành lập của khách hàng doanh nghiệp.",
        None,
        None,
        "Bắt buộc theo quy định KYC. Khách hàng cá nhân phải >= 18 tuổi để mở tài khoản thanh toán. Định dạng: DD/MM/YYYY.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "GENDER",
        "VARCHAR2(1)",
        False,
        False,
        None,
        None,
        "Giới Tính",
        "Giới tính của khách hàng cá nhân. NULL đối với khách hàng doanh nghiệp.",
        None,
        ["M: Nam", "F: Nữ", "O: Khác"],
        "Bắt buộc với CUSTOMER_TYPE = 'INDIVIDUAL'. Phải khớp với giấy tờ tùy thân.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "PHONE_NUMBER",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Số Điện Thoại",
        "Số điện thoại liên hệ chính của khách hàng, dùng cho xác thực OTP và thông báo giao dịch.",
        None,
        None,
        "Định dạng quốc tế: +84xxxxxxxxx. Bắt buộc để đăng ký dịch vụ SMS Banking và Internet Banking. Một số điện thoại chỉ được gắn tối đa 3 CIF.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "EMAIL",
        "VARCHAR2(100)",
        False,
        False,
        None,
        None,
        "Địa Chỉ Email",
        "Địa chỉ email chính của khách hàng, dùng cho gửi sao kê và thông báo điện tử.",
        None,
        None,
        "Phải là email hợp lệ (chứa @). Bắt buộc với khách hàng doanh nghiệp. Tùy chọn với khách hàng cá nhân.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "CUSTOMER_SEGMENT",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Phân Khúc Khách Hàng",
        "Phân khúc khách hàng theo giá trị và quy mô giao dịch, quyết định chính sách ưu đãi.",
        None,
        [
            "MASS: Khách hàng phổ thông",
            "PREMIUM: Khách hàng ưu tiên (AUM >= 1 tỷ VND)",
            "VIP: Khách hàng VIP (AUM >= 5 tỷ VND)",
            "PRIVATE: Khách hàng Private Banking (AUM >= 30 tỷ VND)",
            "SME: Doanh nghiệp vừa và nhỏ",
            "CORPORATE: Doanh nghiệp lớn",
        ],
        "Phân khúc được đánh giá lại hàng quý dựa trên tổng tài sản quản lý (AUM). Mỗi phân khúc có biểu phí và lãi suất ưu đãi riêng.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "RISK_RATING",
        "VARCHAR2(10)",
        False,
        False,
        None,
        None,
        "Mức Xếp Hạng Rủi Ro",
        "Mức xếp hạng rủi ro rửa tiền (AML risk rating) của khách hàng theo quy định phòng chống rửa tiền.",
        None,
        [
            "LOW: Rủi ro thấp",
            "MEDIUM: Rủi ro trung bình",
            "HIGH: Rủi ro cao",
            "PROHIBITED: Cấm giao dịch",
        ],
        "Xếp hạng rủi ro theo Thông tư 09/2023/TT-NHNN về phòng chống rửa tiền. Khách hàng HIGH phải rà soát tăng cường (EDD). Khách hàng PROHIBITED không được phép mở tài khoản mới.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "ONBOARDING_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Mở Quan Hệ",
        "Ngày khách hàng chính thức được tiếp nhận vào hệ thống ngân hàng (ngày mở CIF).",
        None,
        None,
        "Ghi nhận tự động tại thời điểm phê duyệt hồ sơ KYC lần đầu. Không cho phép sửa. Dùng để tính thâm niên quan hệ khách hàng.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_CUSTOMERS",
        "STATUS",
        "VARCHAR2(10)",
        False,
        False,
        None,
        None,
        "Trạng Thái Khách Hàng",
        "Trạng thái hoạt động của hồ sơ khách hàng trong hệ thống.",
        None,
        [
            "ACTIVE: Đang hoạt động",
            "INACTIVE: Ngừng hoạt động (không có giao dịch > 12 tháng)",
            "DORMANT: Tạm ngưng (không có giao dịch > 24 tháng)",
            "BLACKLISTED: Danh sách đen",
            "CLOSED: Đã đóng hồ sơ",
        ],
        "Khách hàng BLACKLISTED bị chặn toàn bộ giao dịch. Khách hàng DORMANT phải đến quầy xác minh lại danh tính trước khi giao dịch tiếp.",
        common=COMMON_CIF,
    ),
]

# ────────────────────────────────────────────────────────────
# (8) CIF_IDENTIFICATIONS – Giấy tờ tùy thân khách hàng
# ────────────────────────────────────────────────────────────
CIF_IDENTIFICATIONS = [
    record(
        "CIF",
        "CIF_IDENTIFICATIONS",
        "IDENTIFICATION_ID",
        "NUMBER(15)",
        True,
        False,
        None,
        None,
        "Mã Giấy Tờ",
        "Khóa chính định danh duy nhất một bản ghi giấy tờ tùy thân.",
        None,
        None,
        "Sinh tự động bởi CIF_IDENTIFICATIONS_SEQ.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_IDENTIFICATIONS",
        "CUSTOMER_ID",
        "NUMBER(15)",
        False,
        True,
        "CIF_CUSTOMERS",
        "CUSTOMER_ID",
        "Mã Khách Hàng",
        "Khóa ngoại trỏ đến khách hàng sở hữu giấy tờ này.",
        None,
        None,
        "Bắt buộc. Mỗi khách hàng phải có ít nhất 1 giấy tờ tùy thân hợp lệ (IS_PRIMARY = 'Y').",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_IDENTIFICATIONS",
        "ID_TYPE",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Loại Giấy Tờ",
        "Loại giấy tờ tùy thân hoặc giấy tờ pháp lý dùng để xác minh danh tính khách hàng.",
        None,
        [
            "CMND: Chứng minh nhân dân",
            "CCCD: Căn cước công dân",
            "PASSPORT: Hộ chiếu",
            "GPKD: Giấy phép kinh doanh",
            "DKKD: Giấy chứng nhận ĐKKD",
            "MILITARY_ID: Chứng minh quân đội",
        ],
        "CMND đã ngừng cấp mới từ 2021. Hệ thống ưu tiên CCCD gắn chip. Đối với khách hàng doanh nghiệp, bắt buộc có GPKD hoặc DKKD.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_IDENTIFICATIONS",
        "ID_NUMBER",
        "VARCHAR2(30)",
        False,
        False,
        None,
        None,
        "Số Giấy Tờ",
        "Số trên giấy tờ tùy thân (VD: số CCCD 12 chữ số, số Hộ chiếu).",
        None,
        None,
        "Phải duy nhất trong phạm vi (ID_TYPE). Không được trùng với bất kỳ khách hàng nào khác. Dùng để tra cứu nhanh và kiểm tra trùng lặp KYC.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_IDENTIFICATIONS",
        "ISSUE_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Cấp",
        "Ngày cấp giấy tờ tùy thân.",
        None,
        None,
        "ISSUE_DATE phải <= ngày hiện tại. Bắt buộc nhập cho tất cả loại giấy tờ.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_IDENTIFICATIONS",
        "EXPIRY_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Hết Hạn",
        "Ngày hết hạn của giấy tờ tùy thân. NULL nếu giấy tờ không có thời hạn (VD: CCCD gắn chip cấp cho người >= 25 tuổi).",
        None,
        None,
        "Hệ thống tự động cảnh báo trước 90 ngày khi giấy tờ sắp hết hạn. Giấy tờ hết hạn phải được cập nhật trước khi khách hàng thực hiện giao dịch lớn.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_IDENTIFICATIONS",
        "ISSUE_PLACE",
        "NVARCHAR2(200)",
        False,
        False,
        None,
        None,
        "Nơi Cấp",
        "Cơ quan cấp giấy tờ tùy thân (VD: Cục Cảnh sát QLHC về TTXH, Sở KH&ĐT TP.HCM).",
        None,
        None,
        "Bắt buộc nhập. Phải khớp với thông tin trên giấy tờ gốc hoặc bản scan lưu trữ.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_IDENTIFICATIONS",
        "IS_PRIMARY",
        "VARCHAR2(1)",
        False,
        False,
        None,
        None,
        "Giấy Tờ Chính",
        "Đánh dấu giấy tờ tùy thân chính dùng cho xác minh danh tính KYC.",
        None,
        ["Y: Là giấy tờ chính", "N: Giấy tờ bổ sung"],
        "Mỗi khách hàng chỉ có đúng 1 giấy tờ IS_PRIMARY = 'Y'. Kiểm soát bởi trigger CIF_ID_PRIMARY_CHECK.",
        common=COMMON_CIF,
    ),
]

# ────────────────────────────────────────────────────────────
# (9) CIF_ADDRESSES – Địa chỉ khách hàng
# ────────────────────────────────────────────────────────────
CIF_ADDRESSES = [
    record(
        "CIF",
        "CIF_ADDRESSES",
        "ADDRESS_ID",
        "NUMBER(15)",
        True,
        False,
        None,
        None,
        "Mã Địa Chỉ",
        "Khóa chính định danh duy nhất một bản ghi địa chỉ.",
        None,
        None,
        "Sinh tự động bởi CIF_ADDRESSES_SEQ.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ADDRESSES",
        "CUSTOMER_ID",
        "NUMBER(15)",
        False,
        True,
        "CIF_CUSTOMERS",
        "CUSTOMER_ID",
        "Mã Khách Hàng",
        "Khóa ngoại trỏ đến khách hàng sở hữu địa chỉ này.",
        None,
        None,
        "Bắt buộc. Mỗi khách hàng phải có ít nhất 1 địa chỉ mặc định (IS_DEFAULT = 'Y').",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ADDRESSES",
        "ADDRESS_TYPE",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Loại Địa Chỉ",
        "Phân loại mục đích sử dụng của địa chỉ.",
        None,
        [
            "HOME: Địa chỉ thường trú",
            "TEMPORARY: Địa chỉ tạm trú",
            "OFFICE: Địa chỉ cơ quan",
            "REGISTERED: Địa chỉ đăng ký kinh doanh",
            "MAILING: Địa chỉ nhận thư",
        ],
        "Khách hàng cá nhân bắt buộc có HOME. Khách hàng doanh nghiệp bắt buộc có REGISTERED. Sao kê gửi đến địa chỉ MAILING (hoặc HOME nếu không có MAILING).",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ADDRESSES",
        "ADDRESS_LINE",
        "NVARCHAR2(500)",
        False,
        False,
        None,
        None,
        "Địa Chỉ Chi Tiết",
        "Dòng địa chỉ chi tiết bao gồm số nhà, tên đường, tổ/ấp/khu phố.",
        None,
        None,
        "Bắt buộc nhập. Tối thiểu 10 ký tự. Phải khớp với địa chỉ trên giấy tờ tùy thân hoặc GPKD.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ADDRESSES",
        "WARD_NAME",
        "NVARCHAR2(100)",
        False,
        False,
        None,
        None,
        "Phường / Xã",
        "Tên phường/xã/thị trấn theo đơn vị hành chính Việt Nam.",
        None,
        None,
        "Phải khớp với danh mục đơn vị hành chính (DMDC) cấp xã do Tổng cục Thống kê ban hành.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ADDRESSES",
        "DISTRICT_NAME",
        "NVARCHAR2(100)",
        False,
        False,
        None,
        None,
        "Quận / Huyện",
        "Tên quận/huyện/thị xã/thành phố thuộc tỉnh theo đơn vị hành chính Việt Nam.",
        None,
        None,
        "Phải khớp với danh mục đơn vị hành chính (DMDC) cấp huyện. Kết hợp DISTRICT + PROVINCE để xác định vùng địa lý.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ADDRESSES",
        "PROVINCE_CODE",
        "VARCHAR2(10)",
        False,
        False,
        None,
        None,
        "Mã Tỉnh / Thành Phố",
        "Mã tỉnh/thành phố trực thuộc trung ương theo chuẩn hành chính quốc gia.",
        None,
        [
            "HN: Hà Nội",
            "HCM: TP. Hồ Chí Minh",
            "DN: Đà Nẵng",
            "HP: Hải Phòng",
            "CT: Cần Thơ",
        ],
        "Dùng để phân vùng địa lý, xác định chi nhánh phục vụ và lập báo cáo phân bổ khách hàng theo địa bàn.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ADDRESSES",
        "IS_DEFAULT",
        "VARCHAR2(1)",
        False,
        False,
        None,
        None,
        "Địa Chỉ Mặc Định",
        "Đánh dấu địa chỉ mặc định dùng cho giao dịch và gửi thư.",
        None,
        ["Y: Là địa chỉ mặc định", "N: Không phải địa chỉ mặc định"],
        "Mỗi khách hàng chỉ có đúng 1 địa chỉ IS_DEFAULT = 'Y'. Kiểm soát bởi trigger CIF_ADDR_DEFAULT_CHECK.",
        common=COMMON_CIF,
    ),
]

# ────────────────────────────────────────────────────────────
# (10) CIF_ACCOUNTS – Liên kết Khách hàng ↔ Tài khoản kế toán
#      (Bảng cầu nối giữa domain CIF và GL)
# ────────────────────────────────────────────────────────────
CIF_ACCOUNTS = [
    record(
        "CIF",
        "CIF_ACCOUNTS",
        "CIF_ACCOUNT_ID",
        "NUMBER(15)",
        True,
        False,
        None,
        None,
        "Mã Liên Kết CIF-Tài Khoản",
        "Khóa chính định danh duy nhất mối quan hệ giữa khách hàng và tài khoản kế toán.",
        None,
        None,
        "Sinh tự động bởi CIF_ACCOUNTS_SEQ. Một khách hàng có thể có nhiều tài khoản và một tài khoản có thể có nhiều đồng sở hữu.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ACCOUNTS",
        "CUSTOMER_ID",
        "NUMBER(15)",
        False,
        True,
        "CIF_CUSTOMERS",
        "CUSTOMER_ID",
        "Mã Khách Hàng",
        "Khóa ngoại trỏ đến khách hàng sở hữu hoặc đồng sở hữu tài khoản.",
        None,
        None,
        "Bắt buộc. Khách hàng phải có STATUS = 'ACTIVE' để mở tài khoản mới.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ACCOUNTS",
        "ACCOUNT_ID",
        "NUMBER(10)",
        False,
        True,
        "GL_ACCOUNTS",
        "ACCOUNT_ID",
        "Mã Tài Khoản GL",
        "Khóa ngoại trỏ đến tài khoản kế toán trong hệ thống GL mà tài khoản khách hàng này hạch toán vào.",
        None,
        None,
        "Đây là CẦU NỐI chính giữa domain Customer (CIF) và domain General Ledger (GL). ACCOUNT_ID phải tham chiếu đến tài khoản cấp 4 (chi tiết) và STATUS = 'ACTIVE'.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ACCOUNTS",
        "ACCOUNT_NUMBER",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Số Tài Khoản Khách Hàng",
        "Số tài khoản riêng biệt của khách hàng tại ngân hàng (hiển thị trên sổ tiết kiệm, sao kê, Internet Banking).",
        None,
        ["VD: 1900 1234 5678 90"],
        "Phải duy nhất toàn hệ thống. Cấu trúc: [Mã CN 4 số] + [Mã SP 4 số] + [Số thứ tự 6 số] + [Check digit 2 số]. Không được tái sử dụng sau khi đóng.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ACCOUNTS",
        "ACCOUNT_ROLE",
        "VARCHAR2(20)",
        False,
        False,
        None,
        None,
        "Vai Trò Sở Hữu",
        "Vai trò của khách hàng đối với tài khoản này.",
        None,
        [
            "OWNER: Chủ tài khoản chính",
            "CO_OWNER: Đồng chủ tài khoản",
            "AUTHORIZED: Người được ủy quyền",
            "BENEFICIARY: Người thụ hưởng",
            "GUARDIAN: Người giám hộ (tài khoản trẻ em)",
        ],
        "Mỗi tài khoản phải có đúng 1 OWNER. CO_OWNER và AUTHORIZED phải có giấy ủy quyền hợp lệ được lưu trong hồ sơ.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ACCOUNTS",
        "OPENING_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Mở Tài Khoản",
        "Ngày tài khoản khách hàng được mở chính thức và bắt đầu nhận giao dịch.",
        None,
        None,
        "Ghi nhận tự động khi hoàn tất quy trình mở tài khoản. OPENING_DATE >= ONBOARDING_DATE của khách hàng.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ACCOUNTS",
        "CLOSING_DATE",
        "DATE",
        False,
        False,
        None,
        None,
        "Ngày Đóng Tài Khoản",
        "Ngày tài khoản bị đóng chính thức. NULL nếu tài khoản đang hoạt động.",
        None,
        None,
        "Tài khoản chỉ được đóng khi số dư = 0 và không có giao dịch chờ xử lý. Không cho phép mở lại tài khoản đã đóng.",
        common=COMMON_CIF,
    ),
    record(
        "CIF",
        "CIF_ACCOUNTS",
        "STATUS",
        "VARCHAR2(10)",
        False,
        False,
        None,
        None,
        "Trạng Thái Tài Khoản",
        "Trạng thái hoạt động của tài khoản khách hàng.",
        None,
        [
            "ACTIVE: Đang hoạt động",
            "FROZEN: Bị phong tỏa (theo yêu cầu cơ quan pháp luật)",
            "DORMANT: Không hoạt động > 12 tháng",
            "CLOSED: Đã đóng",
        ],
        "Tài khoản FROZEN chỉ được gỡ phong tỏa bởi người có thẩm quyền (Giám đốc CN trở lên) kèm văn bản pháp lý. Tài khoản DORMANT bị chặn giao dịch online.",
        common=COMMON_CIF,
    ),
]


# ════════════════════════════════════════════════════════════
# 4. TABLE-LEVEL METADATA  (record_type = TABLE)
# ════════════════════════════════════════════════════════════

TABLE_RECORDS = [
    # ── GL Tables ─────────────────────────────────────────────
    table_record(
        "GL",
        "GL_ACCOUNTS",
        "Danh Mục Tài Khoản Kế Toán",
        "Bảng master lưu trữ hệ thống tài khoản kế toán của ngân hàng theo chuẩn NHNN. Cấu trúc phân cấp 4 cấp (Loại → Nhóm → Tài khoản → Chi tiết).",
        "Tra cứu mã tài khoản, xác định bản chất Nợ/Có, kiểm tra trạng thái hoạt động, phân cấp tổng hợp báo cáo tài chính.",
        "ACCOUNT_ID",
        "ACCOUNT_CODE",
        ["GL_JOURNAL_LINES", "GL_BALANCES", "CIF_ACCOUNTS"],
        "~5,000",
        "Chỉ tài khoản cấp 4 mới được phép hạch toán. Tài khoản kiểm soát nhận số liệu từ sub-ledger.",
    ),
    table_record(
        "GL",
        "GL_PERIODS",
        "Kỳ Kế Toán",
        "Bảng quản lý các kỳ kế toán (tháng) trong năm tài chính. Kiểm soát trạng thái đóng/mở kỳ để cho phép hoặc chặn hạch toán.",
        "Xác định kỳ ghi nhận bút toán, kiểm soát đóng/mở sổ, phục vụ lập báo cáo tài chính theo kỳ.",
        "PERIOD_ID",
        "PERIOD_NAME",
        ["GL_JOURNAL_HEADERS", "GL_BALANCES"],
        "~156 (13 kỳ × 12 năm)",
        "Mỗi năm tài chính có 12 kỳ thường + 1 kỳ điều chỉnh (kỳ 13). Chỉ kỳ OPEN mới nhận bút toán mới.",
    ),
    table_record(
        "GL",
        "GL_COST_CENTERS",
        "Trung Tâm Chi Phí",
        "Bảng master lưu trữ danh mục trung tâm chi phí / đơn vị kinh doanh theo cơ cấu tổ chức nội bộ ngân hàng.",
        "Phân bổ chi phí, lập báo cáo P&L theo đơn vị kinh doanh, phân quyền duyệt bút toán theo đơn vị.",
        "COST_CENTER_ID",
        "COST_CENTER_CODE",
        ["GL_JOURNAL_LINES", "GL_BALANCES"],
        "~500",
        "Phân cấp HO > CN > PGD. Mỗi TTCP thuộc một vùng địa lý (REGION_CODE).",
    ),
    table_record(
        "GL",
        "GL_JOURNAL_HEADERS",
        "Đầu Bút Toán Kế Toán",
        "Bảng lưu trữ thông tin đầu (header) của bút toán kế toán: ngày hạch toán, loại bút toán, trạng thái phê duyệt, hệ thống nguồn.",
        "Ghi nhận chứng từ kế toán, kiểm soát quy trình phê duyệt bút toán, đối chiếu với hệ thống nghiệp vụ nguồn, lập sổ nhật ký chung.",
        "JOURNAL_ID",
        "JOURNAL_NUMBER",
        ["GL_JOURNAL_LINES", "GL_PERIODS"],
        "~2,000,000/năm",
        "TOTAL_DEBIT phải bằng TOTAL_CREDIT (nguyên tắc bút toán kép). Bút toán POSTED không thể xóa, chỉ có thể đảo ngược.",
    ),
    table_record(
        "GL",
        "GL_JOURNAL_LINES",
        "Chi Tiết Dòng Bút Toán",
        "Bảng lưu trữ chi tiết từng dòng ghi Nợ/Có của bút toán kế toán, bao gồm tài khoản, số tiền, trung tâm chi phí, tỷ giá.",
        "Hạch toán chi tiết Nợ/Có vào từng tài khoản, ghi nhận theo trung tâm chi phí, xử lý giao dịch ngoại tệ, đối chiếu với khách hàng.",
        "LINE_ID",
        None,
        ["GL_JOURNAL_HEADERS", "GL_ACCOUNTS", "GL_COST_CENTERS", "CIF_CUSTOMERS"],
        "~10,000,000/năm",
        "Mỗi dòng chỉ ghi Nợ HOẶC Có (không cả hai). DEBIT + CREDIT toàn bộ lines phải cân bằng với header.",
    ),
    table_record(
        "GL",
        "GL_BALANCES",
        "Số Dư Tài Khoản Theo Kỳ",
        "Bảng lưu trữ số dư tài khoản chi tiết theo từng kỳ kế toán, trung tâm chi phí và loại tiền tệ.",
        "Lập Bảng cân đối kế toán, Bảng cân đối tài khoản, Báo cáo kết quả kinh doanh, theo dõi biến động số dư.",
        "BALANCE_ID",
        "(ACCOUNT_ID, COST_CENTER_ID, PERIOD_ID, CURRENCY_CODE)",
        ["GL_ACCOUNTS", "GL_COST_CENTERS", "GL_PERIODS"],
        "~500,000/năm",
        "OPENING = CLOSING kỳ trước. CLOSING_DR và CLOSING_CR không thể cùng > 0. Cập nhật realtime khi POSTING.",
    ),
    # ── CIF Tables ────────────────────────────────────────────
    table_record(
        "CIF",
        "CIF_CUSTOMERS",
        "Thông Tin Khách Hàng",
        "Bảng master lưu trữ thông tin định danh khách hàng (Customer Information File). Bao gồm cả khách hàng cá nhân và doanh nghiệp.",
        "Quản lý hồ sơ KYC, phân khúc khách hàng, đánh giá rủi ro AML, liên kết với tài khoản và giao dịch.",
        "CUSTOMER_ID",
        "CIF_NUMBER",
        ["CIF_IDENTIFICATIONS", "CIF_ADDRESSES", "CIF_ACCOUNTS", "GL_JOURNAL_LINES"],
        "~2,000,000",
        "Mỗi khách hàng có 1 CIF duy nhất. Phân khúc đánh giá hàng quý theo AUM. Rủi ro AML theo Thông tư 09/2023/TT-NHNN.",
        common=COMMON_CIF,
    ),
    table_record(
        "CIF",
        "CIF_IDENTIFICATIONS",
        "Giấy Tờ Tùy Thân Khách Hàng",
        "Bảng lưu trữ thông tin giấy tờ tùy thân / giấy tờ pháp lý của khách hàng phục vụ xác minh danh tính (KYC).",
        "Xác minh danh tính KYC, phát hiện trùng lặp khách hàng, cảnh báo giấy tờ hết hạn.",
        "IDENTIFICATION_ID",
        "(CUSTOMER_ID, ID_TYPE)",
        ["CIF_CUSTOMERS"],
        "~3,000,000",
        "Mỗi KH ít nhất 1 giấy tờ IS_PRIMARY='Y'. Ưu tiên CCCD gắn chip. Cảnh báo trước 90 ngày khi sắp hết hạn.",
        common=COMMON_CIF,
    ),
    table_record(
        "CIF",
        "CIF_ADDRESSES",
        "Địa Chỉ Khách Hàng",
        "Bảng lưu trữ các địa chỉ liên hệ của khách hàng: thường trú, tạm trú, cơ quan, đăng ký kinh doanh.",
        "Gửi sao kê, xác định chi nhánh phục vụ, phân vùng địa lý khách hàng, xác minh KYC.",
        "ADDRESS_ID",
        None,
        ["CIF_CUSTOMERS"],
        "~4,000,000",
        "Mỗi KH phải có ít nhất 1 địa chỉ IS_DEFAULT='Y'. Theo danh mục hành chính quốc gia.",
        common=COMMON_CIF,
    ),
    table_record(
        "CIF",
        "CIF_ACCOUNTS",
        "Liên Kết Khách Hàng – Tài Khoản",
        "Bảng cầu nối (bridge table) giữa domain Customer (CIF) và domain General Ledger (GL). Lưu trữ mối quan hệ sở hữu giữa khách hàng và tài khoản kế toán.",
        "Xác định khách hàng sở hữu tài khoản nào, phân quyền truy cập, liên kết giao dịch GL với hồ sơ khách hàng, lập báo cáo theo khách hàng.",
        "CIF_ACCOUNT_ID",
        "(CUSTOMER_ID, ACCOUNT_ID, ACCOUNT_ROLE)",
        ["CIF_CUSTOMERS", "GL_ACCOUNTS"],
        "~3,000,000",
        "Một KH có thể có nhiều tài khoản; một tài khoản có thể có nhiều đồng sở hữu. Mỗi TK phải có đúng 1 OWNER.",
        common=COMMON_CIF,
    ),
]


# ════════════════════════════════════════════════════════════
# 5. RELATIONSHIP METADATA  (record_type = RELATIONSHIP)
# ════════════════════════════════════════════════════════════

RELATIONSHIP_RECORDS = [
    relationship_record(
        "Chi tiết bút toán kế toán",
        "Truy vấn chi tiết các dòng ghi Nợ/Có của bút toán kế toán. Liên kết header (thông tin chung) với lines (chi tiết) và tên tài khoản.",
        "GL_JOURNAL_HEADERS → GL_JOURNAL_LINES → GL_ACCOUNTS",
        "SELECT h.JOURNAL_NUMBER, h.JOURNAL_DATE, h.DESCRIPTION, "
        "l.LINE_NUMBER, a.ACCOUNT_CODE, a.ACCOUNT_NAME, "
        "l.DEBIT_AMOUNT, l.CREDIT_AMOUNT "
        "FROM GL_JOURNAL_HEADERS h "
        "JOIN GL_JOURNAL_LINES l ON h.JOURNAL_ID = l.JOURNAL_ID "
        "JOIN GL_ACCOUNTS a ON l.ACCOUNT_ID = a.ACCOUNT_ID "
        "WHERE h.STATUS = 'POSTED'",
        ["GL_JOURNAL_HEADERS", "GL_JOURNAL_LINES", "GL_ACCOUNTS"],
        domain="General Ledger",
    ),
    relationship_record(
        "Số dư tài khoản theo kỳ và đơn vị",
        "Truy vấn số dư tài khoản theo kỳ kế toán và trung tâm chi phí. Dùng để lập Bảng cân đối kế toán và Bảng cân đối tài khoản.",
        "GL_BALANCES → GL_ACCOUNTS + GL_PERIODS + GL_COST_CENTERS",
        "SELECT a.ACCOUNT_CODE, a.ACCOUNT_NAME, p.PERIOD_NAME, cc.COST_CENTER_CODE, "
        "b.OPENING_BALANCE_DR, b.PERIOD_ACTIVITY_DR, b.PERIOD_ACTIVITY_CR, b.CLOSING_BALANCE_DR "
        "FROM GL_BALANCES b "
        "JOIN GL_ACCOUNTS a ON b.ACCOUNT_ID = a.ACCOUNT_ID "
        "JOIN GL_PERIODS p ON b.PERIOD_ID = p.PERIOD_ID "
        "JOIN GL_COST_CENTERS cc ON b.COST_CENTER_ID = cc.COST_CENTER_ID "
        "WHERE p.FISCAL_YEAR = 2024",
        ["GL_BALANCES", "GL_ACCOUNTS", "GL_PERIODS", "GL_COST_CENTERS"],
        domain="General Ledger",
    ),
    relationship_record(
        "Bút toán kế toán theo kỳ",
        "Truy vấn danh sách bút toán trong một kỳ kế toán cụ thể. Dùng để lập sổ nhật ký chung và kiểm soát hạch toán.",
        "GL_PERIODS → GL_JOURNAL_HEADERS → GL_JOURNAL_LINES",
        "SELECT p.PERIOD_NAME, h.JOURNAL_NUMBER, h.JOURNAL_TYPE, h.STATUS, "
        "h.TOTAL_DEBIT, h.TOTAL_CREDIT, h.CREATED_BY, h.APPROVED_BY "
        "FROM GL_PERIODS p "
        "JOIN GL_JOURNAL_HEADERS h ON p.PERIOD_ID = h.PERIOD_ID "
        "WHERE p.PERIOD_NAME = '2024-06' AND h.STATUS = 'POSTED'",
        ["GL_PERIODS", "GL_JOURNAL_HEADERS", "GL_JOURNAL_LINES"],
        domain="General Ledger",
    ),
    relationship_record(
        "Giao dịch GL theo khách hàng",
        "Truy vấn cross-domain: từ thông tin khách hàng (CIF) tìm các giao dịch kế toán (GL) liên quan. Đây là cầu nối chính giữa domain Customer và General Ledger.",
        "CIF_CUSTOMERS → CIF_ACCOUNTS → GL_ACCOUNTS → GL_JOURNAL_LINES → GL_JOURNAL_HEADERS",
        "SELECT c.CIF_NUMBER, c.FULL_NAME, ca.ACCOUNT_NUMBER, "
        "h.JOURNAL_NUMBER, h.JOURNAL_DATE, l.DEBIT_AMOUNT, l.CREDIT_AMOUNT "
        "FROM CIF_CUSTOMERS c "
        "JOIN CIF_ACCOUNTS ca ON c.CUSTOMER_ID = ca.CUSTOMER_ID "
        "JOIN GL_ACCOUNTS a ON ca.ACCOUNT_ID = a.ACCOUNT_ID "
        "JOIN GL_JOURNAL_LINES l ON a.ACCOUNT_ID = l.ACCOUNT_ID "
        "JOIN GL_JOURNAL_HEADERS h ON l.JOURNAL_ID = h.JOURNAL_ID "
        "WHERE c.CIF_NUMBER = 'CIF0000000001' AND h.STATUS = 'POSTED'",
        [
            "CIF_CUSTOMERS",
            "CIF_ACCOUNTS",
            "GL_ACCOUNTS",
            "GL_JOURNAL_LINES",
            "GL_JOURNAL_HEADERS",
        ],
        domain="Cross-Domain (CIF ↔ GL)",
    ),
    relationship_record(
        "Hồ sơ đầy đủ khách hàng",
        "Truy vấn toàn bộ thông tin hồ sơ khách hàng bao gồm giấy tờ tùy thân, địa chỉ, và các tài khoản sở hữu.",
        "CIF_CUSTOMERS → CIF_IDENTIFICATIONS + CIF_ADDRESSES + CIF_ACCOUNTS",
        "SELECT c.CIF_NUMBER, c.FULL_NAME, c.CUSTOMER_SEGMENT, "
        "i.ID_TYPE, i.ID_NUMBER, i.EXPIRY_DATE, "
        "a.ADDRESS_TYPE, a.ADDRESS_LINE, a.PROVINCE_CODE, "
        "ca.ACCOUNT_NUMBER, ca.ACCOUNT_ROLE, ca.STATUS "
        "FROM CIF_CUSTOMERS c "
        "LEFT JOIN CIF_IDENTIFICATIONS i ON c.CUSTOMER_ID = i.CUSTOMER_ID "
        "LEFT JOIN CIF_ADDRESSES a ON c.CUSTOMER_ID = a.CUSTOMER_ID "
        "LEFT JOIN CIF_ACCOUNTS ca ON c.CUSTOMER_ID = ca.CUSTOMER_ID "
        "WHERE c.STATUS = 'ACTIVE'",
        ["CIF_CUSTOMERS", "CIF_IDENTIFICATIONS", "CIF_ADDRESSES", "CIF_ACCOUNTS"],
        domain="Customer Information",
    ),
]


# ════════════════════════════════════════════════════════════
# 6. TẬP HỢP TOÀN BỘ DỮ LIỆU
# ════════════════════════════════════════════════════════════

ALL_RECORDS = (
    GL_ACCOUNTS
    + GL_PERIODS
    + GL_COST_CENTERS
    + GL_JOURNAL_HEADERS
    + GL_JOURNAL_LINES
    + GL_BALANCES
    + CIF_CUSTOMERS
    + CIF_IDENTIFICATIONS
    + CIF_ADDRESSES
    + CIF_ACCOUNTS
    + TABLE_RECORDS
    + RELATIONSHIP_RECORDS
)


# ════════════════════════════════════════════════════════════
# 7. HÀM TIỆN ÍCH OPENSEARCH
# ════════════════════════════════════════════════════════════


def _build_embed_text(r: dict) -> str:
    """Tạo chuỗi văn bản đại diện cho document để sinh embedding."""
    rt = r.get("record_type", "COLUMN")
    parts = []
    if rt == "COLUMN":
        parts = [
            f"Bảng {r.get('table_name', '')}",
            f"Cột {r.get('column_name', '')}",
            r.get("business_name", ""),
            r.get("description", ""),
            r.get("business_rules", "") or "",
        ]
    elif rt == "TABLE":
        parts = [
            f"Bảng {r.get('table_name', '')}",
            r.get("business_name", ""),
            r.get("description", ""),
            r.get("table_purpose", "") or "",
            r.get("business_rules", "") or "",
        ]
    elif rt == "RELATIONSHIP":
        parts = [
            r.get("relationship_name", ""),
            r.get("description", ""),
            r.get("join_path", "") or "",
        ]
    return ". ".join(p for p in parts if p)


def create_client():
    """Khởi tạo và trả về OpenSearch client."""
    from opensearchpy import OpenSearch, RequestsHttpConnection

    client = OpenSearch(**_build_opensearch_config(RequestsHttpConnection))
    info = client.info()
    print(
        f"✅ Kết nối thành công: OpenSearch {info['version']['number']} "
        f"| Cluster: {info['cluster_name']}"
    )
    return client


def create_index(client, index_name: str) -> None:
    """Tạo index với mapping. Xóa index cũ nếu tồn tại."""
    if client.indices.exists(index=index_name):
        print(f"⚠️  Index '{index_name}' đã tồn tại. Đang xóa để tạo lại...")
        client.indices.delete(index=index_name)
        time.sleep(1)

    client.indices.create(index=index_name, body=INDEX_MAPPING)
    print(f"✅ Đã tạo index '{index_name}' thành công.")


def _doc_id(r: dict) -> str:
    """Sinh _id duy nhất cho document dựa trên record_type."""
    rt = r.get("record_type", "COLUMN")
    if rt == "TABLE":
        return f"TABLE_{r['table_name']}"
    elif rt == "RELATIONSHIP":
        slug = r.get("relationship_name", "unknown").replace(" ", "_")
        return f"REL_{slug}"
    else:
        return f"{r['table_name']}_{r['column_name']}"


def bulk_index(client, index_name: str, records: list, embed_model) -> None:
    """Nạp dữ liệu hàng loạt vào OpenSearch (bao gồm embedding vectors)."""
    from opensearchpy import helpers
    # Sinh embedding cho toàn bộ records
    texts = [_build_embed_text(r) for r in records]
    print(f"\n🧠 Đang sinh {len(texts)} embeddings với {EMBEDDING_MODEL_NAME}...")
    vectors = embed_model.encode(
        texts, show_progress_bar=True, normalize_embeddings=True
    )
    print(f"✅ Đã sinh xong embeddings (dim={vectors.shape[1]}).")

    actions = [
        {
            "_index": index_name,
            "_id": _doc_id(r),
            "_source": {**r, "description_vector": vec.tolist()},
        }
        for r, vec in zip(records, vectors)
    ]

    print(f"\n📦 Đang nạp {len(actions)} bản ghi vào index '{index_name}'...")
    success, errors = helpers.bulk(client, actions, raise_on_error=False)

    if errors:
        print(f"❌ Có {len(errors)} lỗi khi nạp dữ liệu:")
        for err in errors[:5]:
            print(f"   {err}")
    else:
        print(f"✅ Nạp thành công {success} bản ghi (với vectors).")


def verify_index(client, index_name: str) -> None:
    """Kiểm tra và in thống kê sau khi nạp dữ liệu."""
    time.sleep(2)  # Chờ OpenSearch refresh

    count = client.count(index=index_name)["count"]
    print(f"\n📊 Thống kê index '{index_name}':")
    print(f"   Tổng số bản ghi : {count}")

    # Thống kê theo record_type
    type_result = client.search(
        index=index_name,
        body={
            "size": 0,
            "aggs": {"by_type": {"terms": {"field": "record_type", "size": 10}}},
        },
    )
    print("\n   Theo loại bản ghi:")
    for bucket in type_result["aggregations"]["by_type"]["buckets"]:
        print(f"   ├─ {bucket['key']:<20} {bucket['doc_count']:>4}")

    # Thống kê theo bảng (chỉ COLUMN records)
    agg_result = client.search(
        index=index_name,
        body={
            "size": 0,
            "query": {"term": {"record_type": "COLUMN"}},
            "aggs": {"by_table": {"terms": {"field": "table_name", "size": 20}}},
        },
    )
    print("\n   Cột theo bảng:")
    for bucket in agg_result["aggregations"]["by_table"]["buckets"]:
        print(f"   ├─ {bucket['key']:<30} {bucket['doc_count']:>4} cột")


def demo_search(client, index_name: str, embed_model) -> None:
    """Demo truy vấn – mô phỏng Metadata Agent tìm kiếm Data Dictionary."""
    print("\n" + "═" * 60)
    print("🔍 DEMO: Metadata Agent tìm kiếm Data Dictionary")
    print("═" * 60)

    queries = [
        {
            "desc": "Tìm tất cả cột liên quan đến 'số dư'",
            "body": {
                "query": {
                    "multi_match": {
                        "query": "số dư",
                        "fields": [
                            "business_name^3",
                            "description^2",
                            "business_rules",
                        ],
                    }
                },
                "_source": ["table_name", "column_name", "business_name", "data_type"],
                "size": 5,
            },
        },
        {
            "desc": "Lấy toàn bộ schema bảng GL_JOURNAL_HEADERS",
            "body": {
                "query": {"term": {"table_name": "GL_JOURNAL_HEADERS"}},
                "_source": [
                    "column_name",
                    "data_type",
                    "business_name",
                    "is_primary_key",
                    "is_foreign_key",
                    "description",
                ],
                "sort": [{"column_name": {"order": "asc"}}],
                "size": 20,
            },
        },
        {
            "desc": "Tìm tất cả khóa ngoại trong domain GL",
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"domain_name": "General Ledger"}},
                            {"term": {"is_foreign_key": True}},
                        ]
                    }
                },
                "_source": [
                    "table_name",
                    "column_name",
                    "references_table",
                    "references_column",
                ],
                "size": 20,
            },
        },
        {
            "desc": "Xem cầu nối cross-domain: bảng CIF_ACCOUNTS liên kết Khách hàng ↔ Sổ cái",
            "body": {
                "query": {"term": {"table_name": "CIF_ACCOUNTS"}},
                "_source": [
                    "record_type",
                    "column_name",
                    "data_type",
                    "business_name",
                    "is_foreign_key",
                    "references_table",
                    "references_column",
                ],
                "sort": [{"column_name": {"order": "asc"}}],
                "size": 10,
            },
        },
        {
            "desc": "Tìm TABLE-level metadata: mô tả tổng quan bảng GL_BALANCES",
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"record_type": "TABLE"}},
                            {"term": {"table_name": "GL_BALANCES"}},
                        ]
                    }
                },
                "_source": [
                    "table_name",
                    "business_name",
                    "description",
                    "table_purpose",
                    "primary_key_columns",
                    "natural_key",
                    "related_tables",
                    "estimated_row_count",
                ],
                "size": 1,
            },
        },
        {
            "desc": "Tìm RELATIONSHIP: cách JOIN từ khách hàng sang giao dịch GL",
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"record_type": "RELATIONSHIP"}},
                            {"match": {"description": "khách hàng giao dịch kế toán"}},
                        ]
                    }
                },
                "_source": [
                    "relationship_name",
                    "description",
                    "join_path",
                    "sample_sql",
                    "related_tables",
                ],
                "size": 3,
            },
        },
    ]

    for q in queries:
        print(f"\n▶ {q['desc']}")
        result = client.search(index=index_name, body=q["body"])
        hits = result["hits"]["hits"]
        print(
            f"  Tìm thấy {result['hits']['total']['value']} kết quả. Top {len(hits)}:"
        )
        for hit in hits:
            src = hit["_source"]
            rt = src.get("record_type", "COLUMN")
            if rt == "TABLE":
                print(
                    f"  ├─ [TABLE] {src.get('table_name', '')} – {src.get('business_name', '')}"
                )
                print(f"  │  Mục đích: {src.get('table_purpose', '')[:100]}...")
                print(
                    f"  │  PK: {src.get('primary_key_columns', '')} | Liên kết: {', '.join(src.get('related_tables', []))}"
                )
            elif rt == "RELATIONSHIP":
                print(f"  ├─ [REL] {src.get('relationship_name', '')}")
                print(f"  │  Path: {src.get('join_path', '')}")
                sql = src.get("sample_sql", "")
                print(f"  │  SQL: {sql[:120]}{'...' if len(sql) > 120 else ''}")
            else:
                tbl = src.get("table_name", "")
                col = src.get("column_name", "")
                biz = src.get("business_name", "")
                ref = (
                    f" → {src.get('references_table', '')}.{src.get('references_column', '')}"
                    if src.get("is_foreign_key")
                    else ""
                )
                print(f"  ├─ [COL] {tbl}.{col} ({biz}){ref}")

    # ---- DEMO: Hybrid Search (BM25 + k-NN) ----
    print("\n" + "─" * 60)
    print("🧠 DEMO: Hybrid Search (BM25 keyword + k-NN semantic)")
    print("─" * 60)

    semantic_queries = [
        "tôi muốn xem thông tin tài khoản tiền gửi của khách hàng",
        "làm sao để biết số dư cuối kỳ của một tài khoản",
        "cách kiểm tra bút toán đã được phê duyệt chưa",
    ]

    for sq in semantic_queries:
        print(f'\n▶ Semantic: "{sq}"')
        q_vec = embed_model.encode([sq], normalize_embeddings=True)[0].tolist()

        # Hybrid query: k-NN + BM25 boost
        hybrid_body = {
            "size": 5,
            "_source": [
                "record_type",
                "table_name",
                "column_name",
                "business_name",
                "description",
                "relationship_name",
                "join_path",
            ],
            "query": {
                "bool": {
                    "should": [
                        {
                            "knn": {
                                "description_vector": {
                                    "vector": q_vec,
                                    "k": 5,
                                }
                            }
                        },
                        {
                            "multi_match": {
                                "query": sq,
                                "fields": [
                                    "business_name^3",
                                    "description^2",
                                    "business_rules",
                                    "table_purpose",
                                    "relationship_name^2",
                                ],
                                "boost": 0.3,
                            }
                        },
                    ]
                }
            },
        }

        result = client.search(index=index_name, body=hybrid_body)
        hits = result["hits"]["hits"]
        print(f"  Top {len(hits)} kết quả (score):")
        for hit in hits:
            src = hit["_source"]
            score = hit["_score"]
            rt = src.get("record_type", "COLUMN")
            if rt == "TABLE":
                label = f"[TABLE] {src.get('table_name', '')} – {src.get('business_name', '')}"
            elif rt == "RELATIONSHIP":
                label = f"[REL] {src.get('relationship_name', '')} | {src.get('join_path', '')}"
            else:
                label = f"[COL] {src.get('table_name', '')}.{src.get('column_name', '')} ({src.get('business_name', '')})"
            print(f"  ├─ {score:.4f}  {label}")


# ════════════════════════════════════════════════════════════
# 6. MAIN
# ════════════════════════════════════════════════════════════


def main():
    print("=" * 60)
    print("  OpenSearch GL Data Dictionary – Khởi tạo dữ liệu")
    print("=" * 60)

    # Bước 1: Kết nối
    client = create_client()

    # Bước 2: Load embedding model
    print(f"\n🧠 Đang tải mô hình embedding {EMBEDDING_MODEL_NAME}...")
    from sentence_transformers import SentenceTransformer

    embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print(f"✅ Mô hình embedding sẵn sàng (dim={EMBEDDING_DIM}).")

    # Bước 3: Tạo index
    create_index(client, INDEX_NAME)

    # Bước 4: Nạp dữ liệu (với embeddings)
    bulk_index(client, INDEX_NAME, ALL_RECORDS, embed_model)

    # Bước 5: Kiểm tra
    verify_index(client, INDEX_NAME)

    # Bước 6: Demo tìm kiếm
    demo_search(client, INDEX_NAME, embed_model)

    print("\n✅ Hoàn thành! Data Dictionary đã sẵn sàng cho Metadata Agent.")
    n_col = len([r for r in ALL_RECORDS if r.get("record_type") == "COLUMN"])
    n_tbl = len([r for r in ALL_RECORDS if r.get("record_type") == "TABLE"])
    n_rel = len([r for r in ALL_RECORDS if r.get("record_type") == "RELATIONSHIP"])
    print(
        f"   Index: {INDEX_NAME}  |  COLUMN: {n_col}  |  TABLE: {n_tbl}  |  RELATIONSHIP: {n_rel}  |  Tổng: {len(ALL_RECORDS)}"
    )
    print(f"   Embedding: {EMBEDDING_MODEL_NAME} (dim={EMBEDDING_DIM})")


if __name__ == "__main__":
    main()
