from openai import OpenAI

# Client automatically reads OPENAI_API_KEY from environment
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! What is AI?"}
    ]
)

print(response.choices[0].message.content)