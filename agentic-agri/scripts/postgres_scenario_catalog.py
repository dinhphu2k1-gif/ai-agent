from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioQuestion:
    question_id: str
    question: str
    canonical_sql: str
    min_expected_rows: int = 1


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    business_goal: str
    anchor_tag: str
    questions: tuple[ScenarioQuestion, ...]


SCENARIOS = (
    ScenarioDefinition(
        scenario_id="SCN01",
        business_goal="Khảo sát khách hàng và tài khoản GL sở hữu",
        anchor_tag="SCN01",
        questions=(
            ScenarioQuestion(
                question_id="SCN01_Q1",
                question="Cho tôi danh sách 10 khách hàng đầu tiên trong hệ thống có tag SCN01.",
                canonical_sql="""
                SELECT cif_number, full_name, customer_segment
                FROM cif_customers
                WHERE full_name LIKE '%SCN01%'
                ORDER BY customer_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN01_Q2",
                question="Cho tôi tài khoản của các khách hàng SCN01.",
                canonical_sql="""
                SELECT c.cif_number, c.full_name, ca.account_number, a.account_code
                FROM cif_customers c
                JOIN cif_accounts ca ON c.customer_id = ca.customer_id
                JOIN gl_accounts a ON ca.account_id = a.account_id
                WHERE c.full_name LIKE '%SCN01%'
                ORDER BY c.customer_id, ca.cif_account_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN01_Q3",
                question="Cho tôi journal gần nhất của các tài khoản thuộc khách hàng SCN01.",
                canonical_sql="""
                SELECT c.cif_number, a.account_code, h.journal_number, h.description
                FROM cif_customers c
                JOIN cif_accounts ca ON c.customer_id = ca.customer_id
                JOIN gl_accounts a ON ca.account_id = a.account_id
                JOIN gl_journal_lines l ON l.account_id = a.account_id
                JOIN gl_journal_headers h ON h.journal_id = l.journal_id
                WHERE c.full_name LIKE '%SCN01%'
                ORDER BY h.journal_id DESC
                LIMIT 10
                """,
            ),
        ),
    ),
    ScenarioDefinition(
        scenario_id="SCN02",
        business_goal="Hồ sơ khách hàng đầy đủ",
        anchor_tag="SCN02",
        questions=(
            ScenarioQuestion(
                question_id="SCN02_Q1",
                question="Cho tôi khách hàng SCN02 và số CIF của họ.",
                canonical_sql="""
                SELECT cif_number, full_name, status
                FROM cif_customers
                WHERE full_name LIKE '%SCN02%'
                ORDER BY customer_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN02_Q2",
                question="Cho tôi giấy tờ định danh của khách hàng SCN02.",
                canonical_sql="""
                SELECT c.cif_number, i.id_type, i.id_number, i.is_primary
                FROM cif_customers c
                JOIN cif_identifications i ON c.customer_id = i.customer_id
                WHERE c.full_name LIKE '%SCN02%'
                ORDER BY c.customer_id, i.identification_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN02_Q3",
                question="Cho tôi địa chỉ mặc định của khách hàng SCN02.",
                canonical_sql="""
                SELECT c.cif_number, a.address_type, a.address_line, a.province_code
                FROM cif_customers c
                JOIN cif_addresses a ON c.customer_id = a.customer_id
                WHERE c.full_name LIKE '%SCN02%'
                  AND a.is_default = 'Y'
                ORDER BY c.customer_id
                LIMIT 10
                """,
            ),
        ),
    ),
    ScenarioDefinition(
        scenario_id="SCN03",
        business_goal="Khách hàng active và số dư theo kỳ gần nhất",
        anchor_tag="SCN03",
        questions=(
            ScenarioQuestion(
                question_id="SCN03_Q1",
                question="Cho tôi khách hàng active thuộc scenario SCN03.",
                canonical_sql="""
                SELECT cif_number, full_name, status
                FROM cif_customers
                WHERE full_name LIKE '%SCN03%'
                  AND status = 'ACTIVE'
                ORDER BY customer_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN03_Q2",
                question="Cho tôi tài khoản active của khách hàng SCN03.",
                canonical_sql="""
                SELECT c.cif_number, ca.account_number, ca.status, g.account_code
                FROM cif_customers c
                JOIN cif_accounts ca ON c.customer_id = ca.customer_id
                JOIN gl_accounts g ON ca.account_id = g.account_id
                WHERE c.full_name LIKE '%SCN03%'
                  AND ca.status = 'ACTIVE'
                ORDER BY c.customer_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN03_Q3",
                question="Cho tôi số dư kỳ gần nhất của khách hàng SCN03.",
                canonical_sql="""
                SELECT c.cif_number, g.account_code, p.period_name, b.closing_balance_dr, b.closing_balance_cr
                FROM cif_customers c
                JOIN cif_accounts ca ON c.customer_id = ca.customer_id
                JOIN gl_accounts g ON ca.account_id = g.account_id
                JOIN gl_balances b ON b.account_id = g.account_id
                JOIN gl_periods p ON p.period_id = b.period_id
                WHERE c.full_name LIKE '%SCN03%'
                ORDER BY p.period_id DESC, c.customer_id
                LIMIT 10
                """,
            ),
        ),
    ),
    ScenarioDefinition(
        scenario_id="SCN04",
        business_goal="Theo dõi tài khoản GL và bút toán liên quan",
        anchor_tag="SCN04",
        questions=(
            ScenarioQuestion(
                question_id="SCN04_Q1",
                question="Cho tôi các tài khoản GL thuộc scenario SCN04.",
                canonical_sql="""
                SELECT account_code, account_name, account_type
                FROM gl_accounts
                WHERE account_name LIKE '%SCN04%'
                ORDER BY account_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN04_Q2",
                question="Cho tôi journal lines dùng các tài khoản SCN04.",
                canonical_sql="""
                SELECT a.account_code, l.line_id, l.debit_amount, l.credit_amount
                FROM gl_accounts a
                JOIN gl_journal_lines l ON l.account_id = a.account_id
                WHERE a.account_name LIKE '%SCN04%'
                ORDER BY l.line_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN04_Q3",
                question="Cho tôi journal headers của các line SCN04.",
                canonical_sql="""
                SELECT a.account_code, h.journal_number, h.status, h.description
                FROM gl_accounts a
                JOIN gl_journal_lines l ON l.account_id = a.account_id
                JOIN gl_journal_headers h ON h.journal_id = l.journal_id
                WHERE a.account_name LIKE '%SCN04%'
                ORDER BY h.journal_id
                LIMIT 10
                """,
            ),
        ),
    ),
    ScenarioDefinition(
        scenario_id="SCN05",
        business_goal="Số dư theo cost center",
        anchor_tag="SCN05",
        questions=(
            ScenarioQuestion(
                question_id="SCN05_Q1",
                question="Cho tôi cost center thuộc scenario SCN05.",
                canonical_sql="""
                SELECT cost_center_code, cost_center_name, region_code
                FROM gl_cost_centers
                WHERE cost_center_name LIKE '%SCN05%'
                ORDER BY cost_center_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN05_Q2",
                question="Cho tôi số dư của cost center SCN05.",
                canonical_sql="""
                SELECT cc.cost_center_code, a.account_code, b.closing_balance_dr, b.closing_balance_cr
                FROM gl_cost_centers cc
                JOIN gl_balances b ON b.cost_center_id = cc.cost_center_id
                JOIN gl_accounts a ON a.account_id = b.account_id
                WHERE cc.cost_center_name LIKE '%SCN05%'
                ORDER BY b.balance_id
                LIMIT 10
                """,
            ),
        ),
    ),
    ScenarioDefinition(
        scenario_id="SCN06",
        business_goal="Khách hàng corporate và giao dịch GL",
        anchor_tag="SCN06",
        questions=(
            ScenarioQuestion(
                question_id="SCN06_Q1",
                question="Cho tôi khách hàng corporate thuộc scenario SCN06.",
                canonical_sql="""
                SELECT cif_number, full_name, customer_type
                FROM cif_customers
                WHERE full_name LIKE '%SCN06%'
                  AND customer_type = 'CORPORATE'
                ORDER BY customer_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN06_Q2",
                question="Cho tôi tài khoản của khách hàng corporate SCN06.",
                canonical_sql="""
                SELECT c.cif_number, ca.account_number, g.account_code
                FROM cif_customers c
                JOIN cif_accounts ca ON c.customer_id = ca.customer_id
                JOIN gl_accounts g ON g.account_id = ca.account_id
                WHERE c.full_name LIKE '%SCN06%'
                ORDER BY c.customer_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN06_Q3",
                question="Cho tôi giao dịch GL của khách hàng corporate SCN06.",
                canonical_sql="""
                SELECT c.cif_number, h.journal_number, l.debit_amount, l.credit_amount
                FROM cif_customers c
                JOIN cif_accounts ca ON c.customer_id = ca.customer_id
                JOIN gl_journal_lines l ON l.account_id = ca.account_id
                JOIN gl_journal_headers h ON h.journal_id = l.journal_id
                WHERE c.full_name LIKE '%SCN06%'
                ORDER BY h.journal_id DESC
                LIMIT 10
                """,
            ),
        ),
    ),
    ScenarioDefinition(
        scenario_id="SCN07",
        business_goal="Khách hàng VIP/PREMIUM và account mapping",
        anchor_tag="SCN07",
        questions=(
            ScenarioQuestion(
                question_id="SCN07_Q1",
                question="Cho tôi khách hàng VIP/PREMIUM thuộc SCN07.",
                canonical_sql="""
                SELECT cif_number, full_name, customer_segment
                FROM cif_customers
                WHERE full_name LIKE '%SCN07%'
                  AND customer_segment IN ('VIP', 'PREMIUM')
                ORDER BY customer_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN07_Q2",
                question="Cho tôi account mapping của khách hàng VIP/PREMIUM SCN07.",
                canonical_sql="""
                SELECT c.cif_number, ca.account_number, ca.account_role, g.account_code
                FROM cif_customers c
                JOIN cif_accounts ca ON c.customer_id = ca.customer_id
                JOIN gl_accounts g ON g.account_id = ca.account_id
                WHERE c.full_name LIKE '%SCN07%'
                ORDER BY c.customer_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN07_Q3",
                question="Cho tôi số dư hoặc trạng thái tài khoản của khách hàng SCN07.",
                canonical_sql="""
                SELECT c.cif_number, ca.status, g.account_code, b.closing_balance_dr, b.closing_balance_cr
                FROM cif_customers c
                JOIN cif_accounts ca ON c.customer_id = ca.customer_id
                JOIN gl_accounts g ON g.account_id = ca.account_id
                JOIN gl_balances b ON b.account_id = g.account_id
                WHERE c.full_name LIKE '%SCN07%'
                ORDER BY c.customer_id
                LIMIT 10
                """,
            ),
        ),
    ),
    ScenarioDefinition(
        scenario_id="SCN08",
        business_goal="Báo cáo theo kỳ kế toán",
        anchor_tag="SCN08",
        questions=(
            ScenarioQuestion(
                question_id="SCN08_Q1",
                question="Cho tôi kỳ kế toán thuộc scenario SCN08.",
                canonical_sql="""
                SELECT period_name, fiscal_year, status
                FROM gl_periods
                WHERE period_name LIKE '2026-%'
                ORDER BY period_id DESC
                LIMIT 5
                """,
            ),
            ScenarioQuestion(
                question_id="SCN08_Q2",
                question="Cho tôi journal headers trong kỳ SCN08.",
                canonical_sql="""
                SELECT p.period_name, h.journal_number, h.status, h.description
                FROM gl_periods p
                JOIN gl_journal_headers h ON h.period_id = p.period_id
                WHERE h.description LIKE '%SCN08%'
                ORDER BY h.journal_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN08_Q3",
                question="Cho tôi journal lines thuộc journals SCN08.",
                canonical_sql="""
                SELECT h.journal_number, l.line_id, l.line_description, l.debit_amount, l.credit_amount
                FROM gl_journal_headers h
                JOIN gl_journal_lines l ON l.journal_id = h.journal_id
                WHERE h.description LIKE '%SCN08%'
                ORDER BY l.line_id
                LIMIT 10
                """,
            ),
        ),
    ),
    ScenarioDefinition(
        scenario_id="SCN09",
        business_goal="Theo dõi tài khoản đa tiền tệ",
        anchor_tag="SCN09",
        questions=(
            ScenarioQuestion(
                question_id="SCN09_Q1",
                question="Cho tôi các tài khoản ngoại tệ thuộc SCN09.",
                canonical_sql="""
                SELECT account_code, account_name, currency_code
                FROM gl_accounts
                WHERE account_name LIKE '%SCN09%'
                ORDER BY account_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN09_Q2",
                question="Cho tôi số dư ngoại tệ của các tài khoản SCN09.",
                canonical_sql="""
                SELECT a.account_code, b.currency_code, b.closing_balance_dr, b.closing_balance_cr
                FROM gl_accounts a
                JOIN gl_balances b ON b.account_id = a.account_id
                WHERE a.account_name LIKE '%SCN09%'
                ORDER BY b.balance_id
                LIMIT 10
                """,
            ),
        ),
    ),
    ScenarioDefinition(
        scenario_id="SCN10",
        business_goal="Giám sát tài khoản frozen/dormant/closed",
        anchor_tag="SCN10",
        questions=(
            ScenarioQuestion(
                question_id="SCN10_Q1",
                question="Cho tôi khách hàng SCN10 có account không active.",
                canonical_sql="""
                SELECT c.cif_number, c.full_name, ca.status
                FROM cif_customers c
                JOIN cif_accounts ca ON c.customer_id = ca.customer_id
                WHERE c.full_name LIKE '%SCN10%'
                  AND ca.status IN ('FROZEN', 'DORMANT', 'CLOSED')
                ORDER BY c.customer_id
                LIMIT 10
                """,
            ),
            ScenarioQuestion(
                question_id="SCN10_Q2",
                question="Cho tôi mã account GL của các account không active SCN10.",
                canonical_sql="""
                SELECT c.cif_number, ca.account_number, ca.status, g.account_code
                FROM cif_customers c
                JOIN cif_accounts ca ON c.customer_id = ca.customer_id
                JOIN gl_accounts g ON g.account_id = ca.account_id
                WHERE c.full_name LIKE '%SCN10%'
                  AND ca.status IN ('FROZEN', 'DORMANT', 'CLOSED')
                ORDER BY c.customer_id
                LIMIT 10
                """,
            ),
        ),
    ),
)

SCENARIOS_BY_ID = {scenario.scenario_id: scenario for scenario in SCENARIOS}
