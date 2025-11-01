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
client = httpx.AsyncClient(timeout=10.0)

def format_time():
    return datetime.now(pytz.timezone("US/Eastern")).strftime("%I:%M %p")

async def send(job_id, name, money, players):
    if job_id in seen:
        return
    seen.add(job_id)
    join_link = BASE_JOIN + job_id
    money_str = f"${int(float(money)):,}/s" if money != "unknown" else "unknown"
    embed = {
        "title": name,
        "color": 5814783,
        "fields": [
            {"name": "Money per sec", "value": money_str, "inline": True},
            {"name": "Players", "value": players, "inline": True},
            {"name": "Job-ID (Mobile)", "value": f"||`{job_id}`||", "inline": False},
            {"name": "Job ID (PC)", "value": f"||`{job_id}`||", "inline": False},
            {"name": "Join Link", "value": f"[Click to Join]({join_link})", "inline": False},
            {"name": "Join Script (PC)", "value": f"```lua\ngame:GetService('TeleportService'):TeleportToPlaceInstance(109983668079237, \"{job_id}\", game.Players.LocalPlayer)\n```", "inline": False}
        ],
        "footer": {"text": f"made by hiklo • Today at {format_time()}"}
    }
    try:
        await client.post(WEBHOOK, json={"embeds": [embed]})
        print(f"Sent: {job_id}")
    except Exception as e:
        print(f"Webhook fail: {e}")

async def poll():
    headers = {"Authorization": TOKEN}
    while True:
        try:
            url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=10"
            r = await client.get(url, headers=headers)
            if r.status_code == 401:
                print("Bad TOKEN")
                return
            if r.status_code == 403:
                print("No channel access")
                return
            if r.status_code != 200:
                print(f"HTTP {r.status_code}")
                await asyncio.sleep(1)
                continue

            msgs = r.json()
            tasks = []
            for msg in msgs:
                content = msg.get("content", "")
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                name = "unknown"
                money = "unknown"
                players = "unknown"
                job_id = None

                for line in lines:
                    if line.startswith("Name"):
                        name = line.split("$")[0].replace("Name", "").strip()
                    elif "$" in line and "/s" in line:
                        money = line.split("$")[1].split("/s")[0].strip() + "000000"
                    elif "Players:" in line:
                        players = line.split("Players:")[1].strip().split()[0]

                for emb in msg.get("embeds", []):
                    for field in emb.get("fields", []):
                        if "Job ID" in field.get("name", ""):
                            val = field.get("value", "").strip()
                            if len(val) == 36 and val.replace("-", "").isalnum():
                                job_id = val
                                break
                    if job_id:
                        break

                if job_id:
                    tasks.append(send(job_id, name, money, players))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(0.1)

async def main():
    if not WEBHOOK or not TOKEN:
        print("Set WEBHOOK and TOKEN")
        return
    print("Started. Polling every 0.1s")
    await poll()

if __name__ == "__main__":
    asyncio.run(main())
