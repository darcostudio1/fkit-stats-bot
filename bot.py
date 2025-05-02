import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ROLE = os.getenv("ADMIN_ROLE", "Admin")
STATS_CHANNEL_ID = int(os.getenv("STATS_CHANNEL_ID", "0"))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_stat_fields():
    return [
        ("keep_name", "Keep Name", "text", None),
        ("troop_level", "Troop Level", "dropdown", ["T7", "T8", "T9", "T10", "T11", "T12"]),
        ("keep_level", "Keep Level", "text", None),
        ("march_size", "March Size", "text", "You can find this stat on your march screen when selecting troops for a march. It’s the maximum number of troops you can send in a single march."),
        ("dragon_level", "Dragon Level", "text", None),
        ("house_level", "House Level", "text", None),
        ("rally_cap", "Rally Cap", "text", "This is the maximum number of troops you can rally. You can find it in your rally menu or rally info screen."),
        ("reinforcement_capacity_vs_sop", "Reinforcement Capacity vs SOP", "text", "This is the maximum number of troops you can reinforce at a Seat of Power. Check your keep’s reinforcement info at an SOP."),
        ("troop_type", "Troop Type", "dropdown", ["Infantry", "Range", "Cavalry"]),
        ("marcher_attack_vs_player_sop", "Marcher (Troop) Attack vs Player at SOP", "text", None),
        ("marcher_defense_vs_player_sop", "Marcher (Troop) Defense vs Player at SOP", "text", None),
        ("marcher_health_vs_player_sop", "Marcher (Troop) Health vs Player at SOP", "text", None),
        ("adh_attack_vs_player_sop", "(Troop) Attack vs Player at SOP", "text", None),
        ("adh_defense_vs_player_sop", "(Troop) Defense vs Player at SOP", "text", None),
        ("adh_health_vs_player_sop", "(Troop) Health vs Player at SOP", "text", None),
    ]

# --- Multi-step Modal Implementation ---
from typing import Dict

# Split fields into pages of 5
STAT_FIELDS = get_stat_fields()
STAT_PAGES = [STAT_FIELDS[i:i+5] for i in range(0, len(STAT_FIELDS), 5)]

# Temporary storage for user input between modals (in-memory, per session)
user_modal_data: Dict[int, Dict[str, str]] = {}

class StatModalPage(discord.ui.Modal):
    def __init__(self, alliance, page_num, prev_data=None):
        super().__init__(title=f"Submit Your Stats (Page {page_num+1}/3)")
        self.alliance = alliance
        self.page_num = page_num
        self.prev_data = prev_data or {}
        for field_id, label, input_type, extra in STAT_PAGES[page_num]:
            if input_type == "dropdown":
                self.add_item(discord.ui.TextInput(label=label, placeholder=f"Choose: {', '.join(extra)}", required=True, custom_id=field_id))
            else:
                description = extra if isinstance(extra, str) else None
                self.add_item(discord.ui.TextInput(label=label, placeholder=description or label, required=True, custom_id=field_id))

    async def on_submit(self, interaction: discord.Interaction):
        # Gather data from this page
        data = self.prev_data.copy()
        for item in self.children:
            data[item.custom_id] = item.value
        # If not final page, show next modal
        if self.page_num < len(STAT_PAGES) - 1:
            user_modal_data[interaction.user.id] = data  # Save progress
            await interaction.response.send_modal(StatModalPage(self.alliance, self.page_num + 1, data))
        else:
            # Final page: combine all data
            user_modal_data.pop(interaction.user.id, None)
            all_data = {"discord_id": str(interaction.user.id), "alliance": self.alliance, "last_updated": datetime.now(timezone.utc).isoformat()}
            all_data.update(data)
            for item in self.children:
                all_data[item.custom_id] = item.value
            # Validate dropdowns
            for field_id, label, input_type, extra in STAT_FIELDS:
                if input_type == "dropdown" and all_data[field_id] not in extra:
                    await interaction.response.send_message(f"Invalid value for {label}. Please choose one of: {', '.join(extra)}.", ephemeral=True)
                    return
            # Upsert to Supabase
            supabase.table("player_stats").upsert(all_data, on_conflict=["discord_id"]).execute()
            await interaction.response.send_message("Your stats have been submitted!", ephemeral=True)
            # Optionally update stats table in channel
            if STATS_CHANNEL_ID:
                channel = interaction.guild.get_channel(STATS_CHANNEL_ID)
                if channel:
                    await update_stats_message(channel, interaction.guild)

# Update the /submitstats handler to use the new modal chain
@bot.tree.command(name="submitstats", description="Submit your updated stats")
@app_commands.describe(alliance="Which alliance are you currently in?")
@app_commands.choices(alliance=[
    app_commands.Choice(name="FK!T", value="FK!T"),
    app_commands.Choice(name="SK!T", value="SK!T"),
    app_commands.Choice(name="Recruitment", value="Recruitment"),
])
async def submitstats(interaction: discord.Interaction, alliance: app_commands.Choice[str]):
    await interaction.response.send_modal(StatModalPage(alliance.value, 0))

async def update_stats_message(channel, guild):
    # Fetch all stats
    res = supabase.table("player_stats").select("*").execute()
    rows = res.data or []
    # Format as a table (showing key fields and last updated)
    header = "| Player | Alliance | Keep Level | Troop Level | Dragon | Last Updated |\n|---|---|---|---|---|---|"
    lines = [header]
    for row in rows:
        member = guild.get_member(int(row["discord_id"]))
        name = member.display_name if member else row["discord_id"]
        lines.append(f"| {name} | {row['alliance']} | {row['keep_level']} | {row['troop_level']} | {row['dragon_level']} | {row['last_updated'][:10]} |")
    table = "\n".join(lines)
    # Find or send stats message
    async for msg in channel.history(limit=20):
        if msg.author == guild.me and msg.content.startswith("| Player |"):
            await msg.edit(content=table)
            return
    await channel.send(table)



@bot.tree.command(name="showstats", description="Show the full team stats (admin only)")
async def showstats(interaction: discord.Interaction):
    if not any(role.name == ADMIN_ROLE for role in interaction.user.roles):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    channel = interaction.guild.get_channel(STATS_CHANNEL_ID) or interaction.channel
    await update_stats_message(channel, interaction.guild)
    await interaction.response.send_message("Stats table updated!", ephemeral=True)

@tasks.loop(hours=24)
async def monthly_reminder():
    # Remind players who haven't updated in 30 days
    res = supabase.table("player_stats").select("*").execute()
    now = datetime.now(timezone.utc)
    for row in res.data or []:
        last = datetime.fromisoformat(row["last_updated"].replace("Z", "+00:00"))
        if now - last > timedelta(days=30):
            # DM the user
            guild = bot.guilds[0] if bot.guilds else None
            if guild:
                member = guild.get_member(int(row["discord_id"]))
                if member:
                    try:
                        await member.send("It's time to update your stats for the alliance! Please use /submitstats in the server.")
                    except Exception:
                        pass

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    monthly_reminder.start()

from threading import Thread
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)

