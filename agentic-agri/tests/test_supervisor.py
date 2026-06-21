# test_terminal.py
import uuid
import sys
import time
from dotenv import load_dotenv
from universal_agent.supervisor.graph import app

load_dotenv()


def print_banner():
    print("\n" + "=" * 60)
    print("🚀 SYSTEM MONITOR: UNIVERSAL SUPERVISOR LAYER")
    print("=" * 60)


def render_action_card(state_values):
    """Hiển thị thẻ hành động của Supervisor."""
    intent = state_values.get("intent", "N/A")
    target = state_values.get("target_agent", "N/A")

    print("\n--- 🧠 BẢNG ĐIỀU PHỐI (SUPERVISOR DASHBOARD) ---")
    print(f"🔹 Ý ĐỊNH (Intent):  [{intent.upper()}]")

    if intent == "consult_agent":
        print(f"👉 GIAO VIỆC CHO: 🤖 {target.upper()}")
    elif intent == "ask_user":
        print(f"👉 YÊU CẦU:       Hỏi khách hàng thông tin bổ sung")
    elif intent == "finalize_plan":
        print(f"👉 TRẠNG THÁI:    ✅ Đã chốt kế hoạch thực thi")

    # Hiển thị suy luận cuối cùng
    logs = state_values.get("investigation_log", [])
    if logs:
        # Lọc lấy dòng reasoning gần nhất
        reasoning = [l for l in logs if "Reasoning" in l]
        if reasoning:
            print(
                f"📝 LÝ LUẬN:       {reasoning[-1].replace('Supervisor Reasoning:', '')}"
            )
    print("-" * 50)


def run_monitor():
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print_banner()
    print(f"ID Phiên: {thread_id}")

    while True:
        user_msg = input("\n👤 NHẬP YÊU CẦU: ")
        if user_msg.lower() in ["exit", "quit"]:
            break

        current_input = {
            "user_input": user_msg,
            "investigation_log": [f"Nhận yêu cầu: {user_msg}"],
        }

        # Chạy luồng xử lý và quan sát từng Node
        while True:
            # Lưu vết Node nào đang chạy
            events = app.stream(current_input, config=config, stream_mode="updates")

            for event in events:
                # event sẽ có dạng: {'node_name': {updates}}
                node_name = list(event.keys())[0]
                print(f"\n[NODE]: ⚙️  {node_name.upper()} đang xử lý...")

                # Nếu vừa chạy xong Planner, hãy hiển thị bảng điều phối
                if node_name == "planner":
                    snapshot = app.get_state(config)
                    render_action_card(snapshot.values)

                time.sleep(0.5)  # Tạo độ trễ nhỏ để dễ quan sát

            # Lấy State hiện tại sau mỗi bước
            snapshot = app.get_state(config)
            state_values = snapshot.values

            # Kiểm tra kết quả cuối hoặc HITL
            if state_values.get("final_output") and not snapshot.next:
                print(f"\n✨ KẾT QUẢ CUỐI CÙNG:\n{state_values['final_output']}")
                break

            if snapshot.next and "clarification_node" in snapshot.next:
                print(f"\n❓ AI CẦN HỎI: {state_values.get('message_to_user')}")
                reply = input("👉 PHẢN HỒI: ")
                app.update_state(
                    config,
                    {"investigation_log": [f"Người dùng trả lời (HITL): {reply}"]},
                )
                current_input = None
                continue

            if not snapshot.next:
                break
            current_input = None


if __name__ == "__main__":
    try:
        run_monitor()
    except KeyboardInterrupt:
        sys.exit(0)
