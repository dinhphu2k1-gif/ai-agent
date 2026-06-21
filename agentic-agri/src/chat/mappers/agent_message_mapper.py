"""Map LangGraph supervisor output to FE agent / prompt shapes."""

from __future__ import annotations

from api.schemas.chat import ActionButton, ActionPromptData, ActionPromptOption, TableRow

_SQL_KEYWORDS = ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "WITH ")


def format_final_output_paragraphs(final_output: str) -> list[str]:
    """Turn final_output into paragraph list; fence SQL like Telegram handler."""
    text = (final_output or "").strip()
    if not text:
        return []

    upper = text.upper()
    if any(keyword in upper for keyword in _SQL_KEYWORDS):
        if text.startswith("```"):
            return [text]
        return [f"```sql\n{text}\n```"]

    # Split long metadata / narrative reports for FE (avoid one huge blob).
    chunks = [part.strip() for part in text.split("\n\n") if part.strip()]
    if len(chunks) > 1:
        return chunks
    return [text]


def build_sql_preview_table_events(
    message_id: str, sql_preview: str
) -> list[tuple[str, dict]]:
    """Map SQL worker text preview to optional table + action.buttons SSE events."""
    preview = (sql_preview or "").strip()
    if not preview or "Không có dữ liệu" in preview:
        return []

    lines = [line for line in preview.splitlines() if line.strip()]
    table_header = "Query results"
    table_rows: list[TableRow] = []
    if len(lines) >= 2 and "|" in lines[0]:
        table_header = "SQL preview"
        for line in lines[2:]:
            if "|" not in line:
                continue
            cells = [cell.strip() for cell in line.split("|")]
            if len(cells) < 2:
                continue
            table_rows.append(
                TableRow(
                    region=cells[0][:64],
                    actual=cells[1] if len(cells) > 1 else "",
                    projected=cells[2] if len(cells) > 2 else "",
                    variance=cells[3] if len(cells) > 3 else "",
                    is_positive=True,
                )
            )
    else:
        for idx, line in enumerate(lines[:10]):
            table_rows.append(
                TableRow(
                    region=f"row_{idx + 1}",
                    actual=line[:80],
                    projected="",
                    variance="",
                    is_positive=True,
                )
            )

    events: list[tuple[str, dict]] = []
    if table_rows:
        events.append(
            (
                "table",
                {
                    "messageId": message_id,
                    "tableHeader": table_header,
                    "tableRows": [
                        row.model_dump(by_alias=True) for row in table_rows
                    ],
                },
            )
        )
    events.append(
        (
            "action.buttons",
            {
                "messageId": message_id,
                "buttons": [
                    ActionButton(
                        label="Export CSV",
                        icon="download",
                        action_id="export_csv",
                    ).model_dump(by_alias=True),
                    ActionButton(
                        label="Research Partners",
                        icon="search",
                        action_id="research_partners",
                    ).model_dump(by_alias=True),
                ],
            },
        )
    )
    return events


def build_action_prompt_data(
    message_to_user: str,
    ui_options: list[dict] | None = None,
) -> ActionPromptData:
    """Build action prompt; prefer planner ui_options (2–3 choices) over free-text fallback."""
    description = message_to_user.strip() or (
        "Tôi cần thêm một chút thông tin để có thể giúp bạn tốt hơn."
    )
    options: list[ActionPromptOption] = []
    if ui_options:
        for raw in ui_options[:3]:
            label = str(raw.get("label") or "").strip()
            action_id = str(raw.get("actionId") or raw.get("action_id") or "").strip()
            if label and action_id:
                options.append(
                    ActionPromptOption(label=label, action_id=action_id)
                )
    if not options:
        options = [
            ActionPromptOption(
                label="Option A: Continue analysis",
                action_id="option_a",
            ),
            ActionPromptOption(
                label="Option B: Refine query",
                action_id="option_b",
            ),
            ActionPromptOption(
                label="Option C: Export results",
                action_id="option_c",
            ),
        ]
    return ActionPromptData(
        title="Awaiting your direction",
        description=description,
        options=options,
        custom_option_label="Option D: Custom Input",
    )
