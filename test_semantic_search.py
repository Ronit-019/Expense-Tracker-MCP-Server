import asyncio
from fastmcp import Client


async def main():
    client = Client("main.py")

    async with client:
        tools = await client.list_tools()

        print("AVAILABLE TOOLS:")
        for tool in tools:
            print(f"- {tool.name}")


asyncio.run(main())