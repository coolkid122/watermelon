import httpx
import os
import asyncio
import re
from datetime import datetime
import pytz

WEBHOOK = os.environ.get("WEBHOOK")
TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = "1434273151528734840"
BASE_JOIN = "https://chillihub1.github.io/chillihub-joiner/?placeId=109983668079237&gameInstanceId="

PHRASES = [
    "Chipso and Queso","Los Primos","Eviledon","Los Tacoritas","Tang Tang Keletang",
    "Ketupat Kepat","Tictac Sahur","La Supreme Combinasion","Ketchuru and Musturu",
    "Garama and Madundung","Spaghetti Tualetti","Spooky and Pumpky","La Casa Boo",
    "La Secret Combinasion","Burguro And Fryuro","Headless Horseman",
    "Dragon Cannelloni","Meowl","Strawberry Elephant"
]

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
seen = set()
client = httpx.AsyncClient(timeout=10.0)

def format_time():
    return datetime.now(pytz.timezone("US/Eastern")).strftime("%I:%M %p")

async def send_embed(name, money, players, job_id, is_rare):
    if job_id in seen:
        return
    seen.add(job_id)
    money_str = f"${int(float(money)):,}/s" if money != "unknown" else "unknown"
    color = 16711680 if is_rare else 5814783
    embed = {
        "title": name,
        "color": color,
        "fields": [
            {"name": "Money per sec", "value": money_str, "inline": True},
            {"name": "Players", "value": players, "inline": True},
            {"name": "Job-ID (Mobile)", "value": f"||`{job_id}`||", "inline": False},
            {"name": "Job ID (PC)", "value": f"||`{job_id}`||", "inline": False},
            {"name": "Join Link", "value": f"[Click to Join]({BASE_JOIN}{job_id})", "inline": False},
            {"name": "Join Script (PC)", "value": f"```lua\ngame:GetService('TeleportService'):TeleportToPlaceInstance(109983668079237, \"{job_id}\", game.Players.LocalPlayer)\n```", "inline": False}
        ],
        "footer": {"text": f"made by hiklo • Today at {format_time()}"}
    }
    try:
        await client.post(WEBHOOK, json={"embeds": [embed]})
        print(f"SENT: {job_id} | {name} | {money_str} | {players}")
    except Exception as e:
        print(f"WEBHOOK FAIL: {e}")

async def poll():
    headers = {
        "Authorization": TOKEN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    last_id = None
    print("STARTED. FETCHING MESSAGES...")

    while True:
        try:
            # Always fetch latest 10 messages — no `after` to avoid 404
            url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=10"
            r = await client.get(url, headers=headers)

            if r.status_code == 401:
                print("TOKEN INVALID — CHECK IT")
                return
            if r.status_code == 403:
                print("NO PERMISSION TO READ CHANNEL")
                return
            if r.status_code == 404:
                print("CHANNEL NOT FOUND — WRONG ID")
                return
            if r.status_code != 200:
                print(f"HTTP {r.status_code} — RETRYING...")
                await asyncio.sleep(2)
                continue

            msgs = r.json()
            if not msgs:
                print("NO MESSAGES YET")
                await asyncio.sleep(2)
                continue

            tasks = []
            for msg in reversed(msgs):
                content = msg.get("content", "")
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                name = "unknown"
                money = "unknown"
                players = "unknown"
                job_id = None
                is_rare = any(p.lower() in content.lower() for p in PHRASES)

                # Parse content
                for line in lines:
                    if line.startswith("Name"):
                        name = line.split("$", 1)[0].replace("Name", "").strip()
                    elif "$" in line and "/s" in line:
                        raw = line.split("$")[1].split("/s")[0].strip()
                        money = raw + "000000" if "M" in raw else raw
                    elif "Players:" in line:
                        players = line.split("Players:")[1].strip().split()[0]

                # Extract Job ID from embed
                for emb in msg.get("embeds", []):
                    for field in emb.get("fields", []):
                        if "Job ID" in field.get("name", ""):
                            val = field.get("value", "").strip()
                            if UUID_RE.match(val):
                                job_id = val
                                break
                    if job_id:
                        break

                if job_id and job_id not in seen:
                    tasks.append(send_embed(name, money, players, job_id, is_rare))

            if tasks:
                await asyncio.gather(*tasks)

            # Update last_id only if we have messages
            if msgs:
                last_id = msgs[0]["id"]

        except Exception as e:
            print(f"ERROR: {e}")

        await asyncio.sleep(0.1)  # Fast but safe

async def main():
    if not WEBHOOK:
        print("WEBHOOK MISSING")
        return
    if not TOKEN:
        print("TOKEN MISSING")
        return
    await poll()

if __name__ == "__main__":
    asyncio.run(main())
