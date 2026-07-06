# client.py
# Dew.Ninja  July 2026
# Simple client to test the DHT22_NETPIE MCP server 

from fastmcp import FastMCP
import asyncio
from fastmcp import Client


async def main():
    client = Client("./dht22_netpie_server.py")

    async with client:
        
        # result = await client.call_tool("send_device_command",{"command": "fan=1"})
        # print(result)
        # print()

        result = await client.call_tool("query_temperature")
        print(result.content[0].text)
        print()

        # result = await client.call_tool("start_fan_timer",{"period":10})
        # print(result.content[0].text)
        # print()

        result = await client.call_tool("start_fan_auto",{"maxtemp":40})
        print(result.content[0].text)
        print()


if __name__ == "__main__":
    asyncio.run(main())
