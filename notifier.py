import httpx,os,asyncio,re
from datetime import datetime

WEBHOOK=os.environ.get("WEBHOOK")
RARE=os.environ.get("RARE")
URL="https://autojoinerchered-default-rtdb.europe-west1.firebasedatabase.app/servers.json?auth=AIzaSyBokCjJ7bIUOk_beo2gWQXst6PKqlFFEpc"
BASE_JOIN="https://chillihub1.github.io/chillihub-joiner/?placeId=109983668079237&gameInstanceId="
PHRASES=["Chipso and Queso","Los Primos","Eviledon","Los Tacoritas","Tang Tang Keletang","Ketupat Kepat","Tictac Sahur","La Supreme Combinasion","Ketchuru and Musturu","Garama and Madundung","Spaghetti Tualetti","Spooky and Pumpky","La Casa Boo","La Secret Combinasion","Burguro And Fryuro","Headless Horseman","Dragon Cannelloni","Meowl","Strawberry Elephant"]
BLOCK=re.compile(r"^[0-9A-Fa-f]{100,}$")
seen=set()
client=httpx.AsyncClient(timeout=3.0)

async def send(jid,name,money,players,rare):
    if jid in seen or BLOCK.match(jid):return
    seen.add(jid)
    m=f"${float(money)/1e6:.1f}M/s" if money!="unknown" else "unknown"
    p=players if players!="unknown" else "0/8"
    link=BASE_JOIN+jid
    embed={"title":"Hiklo Corporation | Notify","color":0x00b0f4,"timestamp":datetime.now().isoformat(),"fields":[{"name":"Brainrot","value":name,"inline":True},{"name":"Money per sec","value":m,"inline":True},{"name":"Players","value":p,"inline":False},{"name":"Job ID (Click to Copy)","value":f"```{jid}```","inline":True},{"name":"Join Link","value":f"[Click to Join]({link})","inline":True},{"name":"Join Script (PC)","value":f"```lua\ngame:GetService('TeleportService'):TeleportToPlaceInstance(109983668079237, \"{jid}\", game.Players.LocalPlayer)\n```","inline":False}],"footer":{"text":"made by hiklo"}}
    await client.post(WEBHOOK,json={"embeds":[embed]})
    if rare and RARE:await client.post(RARE,json={"embeds":[embed]})

async def poll():
    while True:
        try:
            r=await client.get(URL)
            if r.status_code!=200:await asyncio.sleep(.01);continue
            data=r.json()
            if not isinstance(data,dict):await asyncio.sleep(.01);continue
            tasks=[]
            for v in data.values():
                j=v.get("jobId")
                if j and j not in seen and not BLOCK.match(j):
                    players=v.get("players","unknown")
                    if players=="unknown":
                        try:
                            job_url=f"https://games.roblox.com/v1/games/109983668079237/servers/Public?sortOrder=Asc&limit=100"
                            job_r=await client.get(job_url)
                            if job_r.status_code==200:
                                job_data=job_r.json()
                                for srv in job_data.get("data",[]):
                                    if srv.get("id")==j:
                                        players=f"{srv.get('playing',0)}/{srv.get('maxPlayers',8)}"
                                        break
                        except:players="0/8"
                    tasks.append(send(j,v.get("name","unknown"),v.get("moneyPerSec","unknown"),players,v.get("name","")in PHRASES))
            if tasks:await asyncio.gather(*tasks)
        except:pass
        await asyncio.sleep(.01)

if __name__=="__main__" and WEBHOOK:
    asyncio.run(poll())
