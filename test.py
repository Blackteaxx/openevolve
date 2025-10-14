from openai import OpenAI

openai_api_key = "token-abc123"
openai_api_base = "http://publicshare.a.pinggy.link/v1"

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

chat_response = client.chat.completions.create(
    model="deepseek-v3",
    messages=[
        {"role": "user", "content": "who are you?"},
    ],
    # max_tokens=32768,
    temperature=0.6,
    top_p=0.95,
)

# 更安全地打印返回内容，避免直接打印对象导致乱码或难以阅读
try:
    print("Chat content:", chat_response.choices[0].message.content)
except Exception:
    print("Chat response:", chat_response)