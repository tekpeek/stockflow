from openai import AsyncOpenAI
import asyncio

client = AsyncOpenAI()

# Non-streaming:
print("----- standard request -----")
async def main():
    completion = await client.chat.completions.create(
    model="gpt-5",
    messages=[
        {
            "role": "user",
            "content": "Say this is a test in a json with key as 'result' and 'status' as 'success'\
                        In case there is any issue in generating response, return 'status' as 'failed'\
                        For now, I want to test the failure scenario",
        },
    ],
    )
    return completion
print(asyncio.run(main()).choices[0].message.content)