import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord import app_commands

TOKEN = os.environ["DISCORD_TOKEN"]
DATA = os.path.join(os.path.dirname(__file__), "links.json")
PORT = int(os.environ.get("PORT", 8080))

with open(DATA, encoding="utf-8") as f:
    APPS = json.load(f)


class Health(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


def mulai_health_server():
    HTTPServer(("0.0.0.0", PORT), Health).serve_forever()


threading.Thread(target=mulai_health_server, daemon=True).start()


def cari(q: str) -> list[dict]:
    q = q.lower()
    return [a for a in APPS if q in a["nama"].lower() or q in a.get("basis", "").lower()]


class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"login sebagai {self.user} | {len(APPS)} entri")


bot = Bot()


def buat_embed(a: dict) -> discord.Embed:
    e = discord.Embed(title=a["nama"], color=0x0B5FFF)
    e.add_field(name="Tipe", value=a.get("tipe", "-"), inline=True)
    e.add_field(name="Basis", value=a.get("basis", "-"), inline=True)
    e.add_field(name="Versi", value=a.get("versi", "-"), inline=True)
    e.add_field(name="Ukuran", value=a.get("ukuran", "-"), inline=True)
    if a.get("catatan"):
        e.add_field(name="Catatan", value=a["catatan"], inline=False)
    return e


def buat_view(a: dict) -> discord.ui.View:
    v = discord.ui.View()
    v.add_item(discord.ui.Button(label="Download", url=a["link"]))
    return v


@bot.tree.command(name="cari", description="Cari app/OS berdasarkan nama")
@app_commands.describe(q="Nama yang dicari")
async def cari_cmd(inter: discord.Interaction, q: str):
    hasil = cari(q)
    if not hasil:
        await inter.response.send_message(f"Ga ada yang cocok sama **{q}**.", ephemeral=True)
        return
    a = hasil[0]
    await inter.response.send_message(embed=buat_embed(a), view=buat_view(a))


class PilihOS(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label=a["nama"], description=f"{a.get('versi', '?')} — {a.get('tipe', '?')}")
            for a in APPS[:25]
        ]
        super().__init__(placeholder="Pilih playbook…", options=opts)

    async def callback(self, inter: discord.Interaction):
        a = next(x for x in APPS if x["nama"] == self.values[0])
        await inter.response.send_message(embed=buat_embed(a), view=buat_view(a), ephemeral=True)


@bot.tree.command(name="download", description="Pilih & download playbook dari daftar")
async def download_cmd(inter: discord.Interaction):
    v = discord.ui.View()
    v.add_item(PilihOS())
    await inter.response.send_message("Pilih playbook yang mau lu download:", view=v, ephemeral=True)


@bot.tree.command(name="list", description="Tampilkan semua yang tersedia")
async def list_cmd(inter: discord.Interaction):
    baris = "\n".join(f"- **{a['nama']}** ({a.get('versi', '?')}) — {a.get('tipe', '?')}" for a in APPS)
    await inter.response.send_message(f"**{len(APPS)} tersedia:**\n{baris}")


@bot.tree.command(name="ping", description="Cek bot hidup")
async def ping_cmd(inter: discord.Interaction):
    await inter.response.send_message(f"pong ({round(bot.latency * 1000)}ms)")


bot.run(TOKEN)
