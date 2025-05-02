# FK!T Stats Bot

A custom Discord bot for Game of Thrones Conquest alliance stat tracking, using Supabase for storage.

## Features
- Players submit stats via slash commands (with dropdowns and text inputs)
- Admins can display a live-updating stats table in a channel
- Monthly DM reminders to players who haven't updated
- Up to 300 players supported

## Setup
1. Clone this repo and install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Create a `.env` file with your Discord bot token and Supabase credentials:
   ```env
   DISCORD_TOKEN=your_discord_token
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   ADMIN_ROLE=AdminRoleName
   STATS_CHANNEL_ID=your_stats_channel_id
   ```
3. Create the `player_stats` table in Supabase using the provided SQL.
4. Run the bot:
   ```sh
   python bot.py
   ```

## Slash Commands
- `/submitstats` — Players enter their stats
- `/showstats` — Admins display/update the stats table

## Customization
- Edit field names or add logic in `bot.py` as needed.
