import os

from dotenv import load_dotenv

load_dotenv()
from telegram import Update
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Nạp LangGraph app
from universal_agent.supervisor.graph import app

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /start"""
    welcome_text = (
        "👋 Xin chào! Tôi là **Universal Supervisor** - Trợ lý AI phân tích dữ liệu đa tác vụ (Multi-Agent).\n\n"
        "Tôi được trang bị hệ thống tra cứu siêu dữ liệu **Data Dictionary (OpenSearch)** và khả năng sinh mã SQL mạnh mẽ. "
        "Chỉ cần cho tôi biết bạn muốn lấy dữ liệu gì, tôi sẽ:\n"
        "1️⃣ Phân tích ngữ nghĩa yêu cầu của bạn.\n"
        "2️⃣ Tìm kiếm lược đồ bảng/cột chuẩn xác nhất.\n"
        "3️⃣ Tự động viết câu lệnh PostgreSQL hoàn chỉnh.\n\n"
        "💡 *Ví dụ:* 'Cho tôi xem danh sách báo cáo chi tiết bút toán kế toán tháng này.'\n\n"
        "Bạn cần truy xuất thông tin gì hôm nay?"
    )
    await update.message.reply_text(welcome_text)


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /reset để xóa trạng thái phiên bộ nhớ hiện tại"""
    await update.message.reply_text(
        "🔄 Đã làm mới bối cảnh trò chuyện. Bạn có câu hỏi mới nào không?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý chat từ người dùng, mang lại trải nghiệm giống ChatGPT."""
    user_msg = update.message.text
    chat_id = str(update.message.chat_id)
    config = {"configurable": {"thread_id": chat_id}}

    # Gửi tin nhắn trạng thái mượt mà giống ChatGPT
    status_message = await update.message.reply_text("⏳ Đang xử lý...")

    # Hiển thị hành động "đang gõ..." trên thanh chat của Telegram
    await context.bot.send_chat_action(
        chat_id=update.message.chat_id, action=ChatAction.TYPING
    )

    # Lấy state snapshot hiện tại để kiểm tra luồng
    snapshot = app.get_state(config)

    # 1. Kiểm tra xem Bot có đang dừng lại ở Clarification / HITL không
    if snapshot.next and "clarification_node" in snapshot.next:
        app.update_state(
            config,
            {"investigation_log": [f"Người dùng trả lời (HITL): {user_msg}"]},
        )
        current_input = None
        status_lines = ["⏳ Đang tiếp tục tiến trình xử lý..."]
    else:
        # Phiên bình thường
        current_input = {
            "user_input": user_msg,
            "investigation_log": [f"Nhận yêu cầu: {user_msg}"],
        }
        status_lines = ["⏳ Bắt đầu khởi tạo luồng tác vụ..."]

    try:
        # Khai báo mapping các bước của HỆ THỐNG
        node_status_map = {
            "planner": "🧠 (Supervisor) Đang phân tích kế hoạch...",
            "metadata_worker_node": "🔄 (metadata_worker_node) Kích hoạt luồng Agent Tra Cứu...",
            "query_analyzer": "🎯 (query_analyzer) Áp dụng thuật toán tìm kiếm...",
            "opensearch_retriever": "🌐 (opensearch_retriever) Gọi truy vấn vào OpenSearch Vector DB...",
            "result_synthesizer": "📝 (result_synthesizer) Lọc và tổng hợp cấu trúc bảng (Schema)...",
            "sql_writer_worker_node": "💻 (sql_writer_worker_node) Đang lập trình thuật toán SQL...",
        }

        # 2. Xử lý Cực Trầm Cảm (astream_events) để quét TẤT CẢ các bước chi tiết bên trong subgraph
        async for event in app.astream_events(
            current_input, config=config, version="v2"
        ):
            kind = event["event"]
            name = event["name"]

            # Bắt sự kiện bắt đầu một Chain/Node bất kỳ (Kể cả bị bóc tách)
            if kind == "on_chain_start":
                friendly_msg = node_status_map.get(name)
                # Chỉ lọc những hàm được thiết kế trong hệ thống
                if friendly_msg and friendly_msg not in status_lines:
                    status_lines.append(friendly_msg)
                    try:
                        await status_message.edit_text("\n".join(status_lines))
                    except:
                        pass

        # 3. Phân Tích Kết Quả Cuối Cùng Sau Stream
        snapshot = app.get_state(config)
        state_values = snapshot.values

        # Nếu hoàn tất tiến trình, sinh ra Output cuối cùng
        if state_values.get("final_output") and not snapshot.next:
            final_out = state_values.get("final_output")

            # Format SQL nếu có
            if (
                "SELECT " in final_out.upper()
                or "INSERT " in final_out.upper()
                or "UPDATE " in final_out.upper()
            ):
                final_out = f"```sql\n{final_out}\n```"

            try:
                await status_message.edit_text(final_out, parse_mode=ParseMode.MARKDOWN)
            except:
                await status_message.edit_text(final_out)

            # Reset final_output trong memory
            app.update_state(config, {"final_output": "", "message_to_user": ""})

        # Nếu hệ thống dừng dở dang và yêu cầu xin ý kiến khách hàng (Human in the loop)
        elif snapshot.next and "clarification_node" in snapshot.next:
            question = state_values.get(
                "message_to_user",
                "Tôi cần thêm một chút thông tin để có thể giúp bạn tốt hơn.",
            )
            try:
                await status_message.edit_text(question, parse_mode=ParseMode.MARKDOWN)
            except:
                await status_message.edit_text(question)

    except Exception as e:
        error_msg = f"⚠️ Xin lỗi, đã có lỗi xảy ra: {str(e)}"
        print(error_msg)
        try:
            await status_message.edit_text(error_msg)
        except:
            pass


async def _init_supervisor_graph(_application) -> None:
    from universal_agent.supervisor.graph import setup_supervisor_checkpointer

    await setup_supervisor_checkpointer()


def main():
    """Khởi động Telegram Bot"""
    if not TELEGRAM_BOT_TOKEN:
        print("Lỗi: Không tìm thấy TELEGRAM_BOT_TOKEN trong file .env")
        return

    app_bot = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(_init_supervisor_graph)
        .build()
    )

    # Đăng ký các handler
    app_bot.add_handler(CommandHandler("start", start_command))
    app_bot.add_handler(CommandHandler("reset", reset_command))
    app_bot.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )

    print("🚀 Telegram Bot đang khởi động... Bấm Ctrl+C để thoát.")
    app_bot.run_polling()


if __name__ == "__main__":
    main()
