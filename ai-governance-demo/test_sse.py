import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", "http://localhost:8000/api/chat", json={"question": "Cho tôi xem danh sách toàn bộ khách hàng và số dư tài khoản của họ", "user_id": "teller_hn"}) as resp:
            buffer = ""
            async for chunk in resp.aiter_text():
                buffer += chunk
                lines = buffer.split('\n')
                buffer = lines.pop()
                for line in lines:
                    print(repr(line))

asyncio.run(test())
