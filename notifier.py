import httpx
import os
import asyncio
import json
from datetime import datetime
import pytz

WEBHOOK = os.environ.get("WEBHOOK")
TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = "1434273151528734840"
BASE_JOIN = "https://chillihub1.github.io/chillihub-joiner/?placeId=109983668079237&gameInstanceId="

seen = set()
client = httpx.AsyncClient(timeout=5.0, limits=httpx.Limits(max_connections=200, max_keepalive_connections=50))

def format_time():
    return datetime.now(pytz.timezone("US/Eastern")).strftime("%I:%M %p")

async def send_embed(data):
    job_id = data["jobId"]
    join_link = BASE_JOIN + job_id
    name = data["name"]
    money = f"${int(float(data['moneyPerSec'])):,}/s" if data["moneyPerSec"] != "unknown" else "unknown"
    players = data["players"]
    time_str = format_time()

    embed = {
        "title": name,
        "color": 5814783,
        "fields": [
            {"name": "Money per sec", "value": money, "inline": True},
            {"name": "Players", "value": players, "inline": True},
            {"name": "Job-ID (Mobile)", "value": f"||`{job_id}`||", "inline": False},
            {"name": "Job ID (PC)", "value": f"||`{job_id}`||", "inline": False},
            {"name": "Join Link", "value": f"[Click to Join]({join_link})", "inline": False},
            {"name": "Join Script (PC)", "value": f"```lua\ngame:GetService('TeleportService'):TeleportToPlaceInstance(109983668079237, \"{job_id}\", game.Players.LocalPlayer)\n```", "inline": False}
        ],
        "footer": {"text": f"made by hiklo • Today at {time_str}"}
    }
    try:
        await client.post(WEBHOOK, json={"embeds": [embed]})
    except Exception as e:
        print("Webhook error:", e)

async def poll():
    headers = {
        "Authorization": TOKEN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    last_id = None
    while True:
        try:
            url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=50"
            if last_id:
                url += f"&after={last_id}"
            r = await client.get(url, headers=headers)
            if r.status_code == 401:
                print("Invalid token")
                return
            if r.status_code == 403:
                print("No access to channel")
                return
            if r.status_code != 200:
                await asyncio.sleep(1)
                continue
            msgs = r.json()
            if not msgs:
                await asyncio.sleep(1)
                continue

            tasks = []
            for msg in reversed(msgs):
                content = msg.get("content", "")
                embeds = msg.get("embeds", [])
                job_id = None
                name = "unknown"
                money = "unknown"
                players = "unknown"

                # Extract from content
                lines = content.splitlines()
                for line in lines:
                    if line.startswith("Name"):
                        name = line.split("$", 1)[0].replace("Name", "").strip()
                    elif "$" in line and "/s" in line:
                        money = line.split("$")[1].split("/s")[0].strip() + "000000"
                    elif "Players:" in line:
                        players = line.split("Players:")[1].strip().split()[0]

                # Extract job ID from embed fields
                for emb in embeds:
                    for field in emb.get("fields", []):
                        if "Job ID" in field.get("name", ""):
                            val = field.get("value", "").strip()
                            if len(val) == 36 and val.replace("-", "").isalnum():
                                job_id = val
                                break
                    if job_id:
                        break

                if job_id and job_id not in seen:
                    seen.add(job_id)
                    data = {
                        "jobId": job_id,
                        "name": name,
                        "moneyPerSec": money,
                        "players": players
                    }
                    tasks.append(send_embed(data))

                last_id = msg["id"]

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            print("Poll error:", e)
        await asyncio.sleep(0.5)

async def main():
    if not WEBHOOK or not TOKEN:
        print("Missing WEBHOOK or TOKEN")
        return
    print("Notifier started. Polling every 0.5s...")
    await poll()

if __name__ == "__main__":
    asyncio.run(main())
