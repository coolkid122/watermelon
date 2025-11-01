import httpx
import os
import asyncio
import re
from datetime import datetime
import pytz

WEBHOOK = os.environ.get("WEBHOOK")
RARE = os.environ.get("RARE")
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
    join_link = BASE_JOIN + job_id
    embed = {
        "title": name,
        "color": color,
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
    payload = {"embeds": [embed]}

    # Send to main WEBHOOK
    if WEBHOOK:
        try:
            await client.post(WEBHOOK, json=payload)
            print(f"SENT (main): {name} | {money_str} | {players}")
        except Exception as e:
            print(f"MAIN WEBHOOK ERROR: {e}")

    # Send to RARE if rare
    if is_rare and RARE:
        try:
            await client.post(RARE, json=payload)
            print(f"SENT (rare): {name} | {money_str} | {players}")
        except Exception as e:
            print(f"RARE WEBHOOK ERROR: {e}")

async def poll():
    headers = {"Authorization": TOKEN}
    last_id = None
    print("MONITORING CHANNEL...")
    while True:
        try:
            url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=10"
            if last_id:
                url += f"&after={last_id}"
            r = await client.get(url, headers=headers)

            if r.status_code == 401:
                print("INVALID TOKEN")
                return
            if r.status_code == 403:
                print("NO CHANNEL ACCESS")
                return
            if r.status_code != 200:
                print(f"HTTP {r.status_code}")
                await asyncio.sleep(1)
                continue

            msgs = r.json()
            tasks = []
            for msg in reversed(msgs):
                content = msg.get("content", "")
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                name = "unknown"
                money = "unknown"
                players = "unknown"
                job_id = None
                is_rare = any(p.lower() in content.lower() for p in PHRASES)

                for line in lines:
                    if line.startswith("Name"):
                        name = line.split("$", 1)[0].replace("Name", "").strip()
                    elif "$" in line and "/s" in line:
                        raw = line.split("$")[1].split("/s")[0].strip()
                        money = raw + "000000" if "M" in raw else raw
                    elif "Players:" in line:
                        players = line.split("Players:")[1].strip().split()[0]

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

                last_id = msg["id"]

            if tasks:
                await asyncio.gather(*tasks)

        except Exception as e:
            print(f"POLL ERROR: {e}")
        await asyncio.sleep(0.1)

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
