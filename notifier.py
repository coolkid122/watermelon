import httpx
import os
import asyncio
from datetime import datetime
import pytz

WEBHOOK = os.environ.get("WEBHOOK")
TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = "1434273151528734840"
BASE_JOIN = "https://chillihub1.github.io/chillihub-joiner/?placeId=109983668079237&gameInstanceId="

seen_msg = set()
seen_job = set()
client = httpx.AsyncClient(timeout=5.0, limits=httpx.Limits(max_connections=200, max_keepalive_connections=50))

def format_time():
    return datetime.now(pytz.timezone("US/Eastern")).strftime("%I:%M %p")

async def send_embed(data):
    job_id = data.get("jobId", "unknown")
    if job_id == "unknown" or len(job_id) != 36 or job_id in seen_job:
        return
    seen_job.add(job_id)
    join_link = BASE_JOIN + job_id
    name = data.get("name", "unknown")
    money = data.get("moneyPerSec", "unknown")
    if money != "unknown":
        money = f"${int(float(money)):,}/s"
    players = data.get("players", "unknown")
    footer_time = format_time()

    mobile_copy = f"||`{job_id}`||"
    pc_copy = f"||`{job_id}`||"

    embed = {
        "title": name,
        "color": 5814783,
        "fields": [
            {"name": "Money per sec", "value": money, "inline": True},
            {"name": "Players", "value": players, "inline": True},
            {"name": "Job-ID (Mobile)", "value": mobile_copy, "inline": False},
            {"name": "Job ID (PC)", "value": pc_copy, "inline": False},
            {"name": "Join Link", "value": f"[Click to Join]({join_link})", "inline": False},
            {"name": "Join Script (PC)", "value": f"```lua\ngame:GetService('TeleportService'):TeleportToPlaceInstance(109983668079237, \"{job_id}\", game.Players.LocalPlayer)\n```", "inline": False}
        ],
        "footer": {"text": f"made by hiklo • Today at {footer_time}"}
    }
    payload = {"embeds": [embed]}
    try:
        await client.post(WEBHOOK, json=payload)
    except:
        pass

async def poll():
    global seen_msg
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    last_id = None
    while True:
        try:
            url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=50"
            if last_id:
                url += f"&after={last_id}"
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                await asyncio.sleep(0.5)
                continue
            msgs = r.json()
            if not msgs:
                await asyncio.sleep(0.5)
                continue
            tasks = []
            for msg in reversed(msgs):
                if msg["id"] in seen_msg:
                    continue
                seen_msg.add(msg["id"])
                for emb in msg.get("embeds", []):
                    for field in emb.get("fields", []):
                        val = field.get("value", "")
                        name_field = field.get("name", "")
                        if "Job ID" in name_field or "jobId" in val:
                            job_id_match = val.strip()
                            if len(job_id_match) == 36:
                                content = msg.get("content", "")
                                extracted_name = "unknown"
                                extracted_money = "unknown"
                                extracted_players = "unknown"
                                lines = content.splitlines()
                                for line in lines:
                                    if line.startswith("Name"):
                                        extracted_name = line.split("$", 1)[0].replace("Name", "").strip()
                                    elif "$" in line and "/s" in line:
                                        extracted_money = line.split("$")[1].split("/s")[0].strip() + "000000"
                                    elif "Players:" in line:
                                        extracted_players = line.split("Players:")[1].strip().split()[0]
                                data = {
                                    "jobId": job_id_match,
                                    "name": extracted_name,
                                    "moneyPerSec": extracted_money,
                                    "players": extracted_players
                                }
                                tasks.append(send_embed(data))
                last_id = msg["id"]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        except:
            pass
        await asyncio.sleep(0.01)

async def main():
    if not WEBHOOK or not TOKEN:
        return
    await poll()

if __name__ == "__main__":
    asyncio.run(main())
