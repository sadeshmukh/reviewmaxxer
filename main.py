import asyncio
import json
import logging
import os

import aiohttp
from utils import _env

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler

from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(level=logging.INFO)

app = AsyncApp(
    token=_env("XOXB"),
)

# CMD_BASE = _env("CMD", "")
SESSION = _env("SESSION")
cleared = []


async def notify_slack(item):
    ping_text = f"Hey {_env('PING')}, " if _env("PING") else ""
    await app.client.chat_postMessage(
        channel=_env("NOTIFY_CHANNEL"),
        text=f"{ping_text} https://horizons.hackclub.com/admin/review/{item.get('project', {}).get('projectId')}",
    )


async def notify_ntfy(item):
    review_url = f"https://horizons.hackclub.com/admin/review/{item.get('project', {}).get('projectId')}"
    headers = {
        "Title": f"New {item.get('project', {}).get('projectType', 'UH OH')} submission",
        # TBD tags
        "Click": review_url,
        # "Markdown": "yes",
        "Actions": f"view, go go go!, {review_url}",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        await session.post(
            f"https://ntfy.sh/{_env('NTFY')}",
            data=review_url,
        )


async def notify(item):
    logging.info(f"[cleared]: {item.get('project', {}).get('projectId')}")
    await notify_slack(item)
    await notify_ntfy(item)


async def serialize_cleared():
    global cleared

    with open("cleared.json", "w") as f:
        json.dump(cleared, f)


async def refresh_cleared():
    global cleared

    cookies = {"sessionId": SESSION}
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(
            f"https://horizons.hackclub.com/api/reviewer/queue"
        ) as res:
            data = await res.json()
            for item in data:
                if item.get("project", {}).get("projectId") not in cleared:
                    await notify(item)
                    cleared = [i.get("project", {}).get("projectId") for i in data]
                    await serialize_cleared()


async def periodic():
    while True:
        await refresh_cleared()
        await asyncio.sleep(30)


async def main():
    global cleared
    if os.path.exists("cleared.json"):
        with open("cleared.json", "r") as f:
            cleared = json.load(f)
    asyncio.create_task(periodic())
    handler = AsyncSocketModeHandler(app, _env("XAPP"))
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(
    #     notify_ntfy({"project": {"projectType": "Test", "projectId": 123}}})
    # )
