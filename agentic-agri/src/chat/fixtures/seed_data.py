"""Golden fixture from chat-sse-be-spec.md §4.2 / §12 (FE getInitialMessages)."""

from __future__ import annotations

from api.schemas.chat import (
    ActionButton,
    ActionPromptData,
    ActionPromptOption,
    AgentMessageData,
    Channel,
    ExecutionTraceStep,
    Message,
    TableRow,
)

CHANNELS: list[Channel] = [
    Channel(
        id="threat-intel",
        title="threat-intel-global",
        icon="shield",
        category="Active Channels",
    ),
    Channel(
        id="network-anomaly",
        title="network-anomaly-detect",
        icon="hub",
        category="Active Channels",
    ),
    Channel(
        id="insider-risk",
        title="insider-risk-alerts",
        icon="person_alert",
        category="Active Channels",
    ),
    Channel(
        id="market-trends",
        title="Market Trends",
        icon="trending_up",
        category=None,
    ),
]

MARKET_TRENDS_MESSAGES: list[Message] = [
    Message(
        id="msg-system-001",
        sender="system",
        timestamp="2026-05-20T10:30:00+07:00",
        content=(
            "Channel policy: revenue analysis uses read-only warehouse data. "
            "Do not share credentials in chat."
        ),
    ),
    Message(
        id="msg-001",
        sender="user",
        timestamp="2026-05-20T10:40:00+07:00",
        content=(
            "Analyze the latest Q4 revenue trends for the European sector, "
            "focusing on variance against projections."
        ),
    ),
    Message(
        id="msg-002",
        sender="agent",
        timestamp="2026-05-20T10:42:00+07:00",
        agent_data=AgentMessageData(
            execution_trace=[
                ExecutionTraceStep(
                    title="Invoking Search Tool",
                    description="Querying Q4 European sales database for UK&I, DACH, Nordics.",
                    icon="search",
                ),
                ExecutionTraceStep(
                    title="Aggregating Results",
                    description="Computing variance vs projected targets by region.",
                    icon="dataset",
                ),
            ],
            paragraphs=[
                "I've compiled the Q4 revenue data for the European sector. "
                "UK & Ireland exceeded projections while DACH underperformed relative to plan."
            ],
            table_header="Q4_EU_Revenue_Summary.csv",
            table_rows=[
                TableRow(
                    region="UK & Ireland",
                    actual="€42.5",
                    projected="€41.0",
                    variance="+3.6%",
                    is_positive=True,
                ),
                TableRow(
                    region="DACH",
                    actual="€68.2",
                    projected="€75.5",
                    variance="-9.6%",
                    is_positive=False,
                ),
                TableRow(
                    region="Nordics",
                    actual="€31.4",
                    projected="€30.0",
                    variance="+4.7%",
                    is_positive=True,
                ),
            ],
            action_buttons=[
                ActionButton(
                    label="Research Partners",
                    icon="search",
                    action_id="research_partners",
                ),
                ActionButton(
                    label="Export CSV",
                    icon="download",
                    action_id="export_csv",
                ),
            ],
        ),
    ),
    Message(
        id="msg-003",
        sender="action_prompt",
        timestamp="2026-05-20T10:43:00+07:00",
        prompt_data=ActionPromptData(
            title="Awaiting your direction",
            description="Based on the Q4 data, how should we proceed?",
            options=[
                ActionPromptOption(
                    label="Option A: Region Audit",
                    action_id="option_a",
                ),
                ActionPromptOption(
                    label="Option B: Partner Review",
                    action_id="option_b",
                ),
                ActionPromptOption(
                    label="Option C: Forecast Adjustment",
                    action_id="option_c",
                ),
            ],
            custom_option_label="Option D: Custom Input",
        ),
    ),
]

MESSAGES_BY_CHANNEL: dict[str, list[Message]] = {
    "market-trends": MARKET_TRENDS_MESSAGES,
}
