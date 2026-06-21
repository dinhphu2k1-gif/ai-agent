"""
Utility functions dùng chung cho toàn bộ hệ thống agent.
"""


def get_text_content(response) -> str:
    """
    Lấy text an toàn từ AIMessage content.
    Xử lý trường hợp content là string hoặc list.
    """
    content = response.content
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
        return "".join(parts)
    return str(content)


def strip_markdown_json(text: str) -> str:
    """Xoá ```json ... ``` wrapper mà LLM hay sinh ra."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()
