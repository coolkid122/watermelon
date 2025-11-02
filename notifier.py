import httpx
import os
import asyncio
from datetime import datetime
import pytz

WEBHOOK = os.environ.get("WEBHOOK")
RARE = os.environ.get("RARE")
URL = "https://autojoinerchered-default-rtdb.europe-west1.firebasedatabase.app/servers.json?auth=AIzaSyBokCjJ7bIUOk_beo2gWQXst6PKqlFFEpc"
BASE_JOIN = "https://chillihub1.github.io/chillihub-joiner/?placeId=109983668079237&gameInstanceId="

PHRASES = [
    "Chipso and Queso","Los Primos","Eviledon","Los Tacoritas","Tang Tang Keletang",
    "Ketupat Kepat","Tictac Sahur","La Supreme Combinasion","Ketchuru and Musturu",
    "Garama and Madundung","Spaghetti Tualetti","Spooky and Pumpky","La Casa Boo",
    "La Secret Combinasion","Burguro And Fryuro","Headless Horseman",
    "Dragon Cannelloni","Meowl","Strawberry Elephant"
]

seen = set()
client = httpx.AsyncClient(timeout=5.0)

async def send_embed(name, money_str, players, job_id, is_rare):
    if job_id in seen:
        return
    seen.add(job_id)
    join_link = BASE_JOIN + job_id
    embed = {
        "title": "Hiklo Corporation | Notify",
        "color": 0x00b0f4,
        "timestamp": datetime.now().isoformat(),
        "fields": [
            {"name": "Brainrot", "value": name, "inline": True},
            {"name": "Money per sec", "value": money_str, "inline": True},
            {"name": "Players", "value": players, "inline": False},
            {"name": "Job ID (Mobile)", "value": f"||`{job_id}`||", "inline": True},
            {"name": "Job ID (PC)", "value": f"||`{job_id}`||", "inline": True},
            {"name": "Join Link", "value": f"[Click to Join]({join_link})", "inline": True},
            {"name": "Join Script (PC)", "value": f"```lua\ngame:GetService('TeleportService'):TeleportToPlaceInstance(109983668079237, \"{job_id}\", game.Players.LocalPlayer)\n```", "inline": False}
        ],
        "footer": {"text": "made by hiklo"}
    }
    payload = {"embeds": [embed]}
    await client.post(WEBHOOK, json=payload)
    if is_rare and RARE:
        await client.post(RARE, json=payload)

async def poll():
    while True:
        r = await client.get(URL)
        data = r.json()
        tasks = []
        for val in data.values():
            job = val.get("jobId")
            if job and job not in seen:
                name = val.get("name", "unknown")
                money = val.get("moneyPerSec", "unknown")
                players = val.get("players", "?/8")
                money_str = f"${float(money)/1000000:.1f}M/s" if money != "unknown" else "unknown"
                is_rare = name in PHRASES
                tasks.append(send_embed(name, money_str, players, job, is_rare))
        if tasks:
            await asyncio.gather(*tasks)
        await asyncio.sleep(0.01)

async def main():
    await poll()

if __name__ == "__main__":
    asyncio.run(main())
