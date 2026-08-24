import asyncio
from datetime import datetime, timezone
import os
import discord
from discord.ext import commands

# CONFIGURATION (Reads TOKEN securely from Railway Environment Variables)
TOKEN = os.getenv("TOKEN")
USER_ID = 1517621685745090633
SOURCE_CHANNEL_ID = 1522401003100442726
SOURCE_MESSAGE_ID = 1541218162224144404
message_content = "Good morning!"

blocked_user_ids = [
    760963355803516928,
    1524073576947519570,
    1086367366226653365,
    1235696424482770995,
    1518999747812130981,
    1492096025752764467,
    1260308483505389721,
]

forced_user_ids = set()
stats = {"last_success": 0, "last_skipped": 0, "last_failed": 0, "total_runs": 0}
max_days_inactive = 2

# Initialize selfbot client
bot = commands.Bot(command_prefix="", self_bot=True)


async def run_broadcast(trigger_source="Manual Command"):
  print(f"\n--- Starting DM Broadcast ({trigger_source}) ---")
  success_count = 0
  skip_count = 0
  fail_count = 0
  current_time_ms = datetime.now(timezone.utc).timestamp() * 1000

  for channel in bot.private_channels:
    if isinstance(channel, discord.DMChannel):
      user_id = channel.recipient.id

      if user_id in blocked_user_ids:
        skip_count += 1
        continue

      if user_id in forced_user_ids:
        print(f"Bypassing inactivity filter [Forced User]: {channel.recipient.name}")
      else:
        try:
          async for msg in channel.history(limit=1):
            last_msg_time = msg.created_at.timestamp() * 1000
            days_inactive = (
                current_time_ms - last_msg_time
            ) / (1000 * 60 * 60 * 24)
            if days_inactive > max_days_inactive:
              skip_count += 1
              break
          else:
            skip_count += 1
            continue
        except Exception:
          fail_count += 1
          continue

      try:
        await channel.send(message_content)
        print(f"Successfully sent to DM: {channel.recipient.name}")
        success_count += 1
        await asyncio.sleep(2)
      except Exception:
        fail_count += 1

  stats["last_success"] = success_count
  stats["last_skipped"] = skip_count
  stats["last_failed"] = fail_count
  stats["total_runs"] += 1
  print(
      f"--- Task completed! Success: {success_count} | Skipped: {skip_count} |"
      f" Failed: {fail_count} ---\n"
  )


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
  print("Python Selfbot is online and ready!")
  bot.loop.create_task(daily_timer_loop())


async def daily_timer_loop():
  await bot.wait_until_ready()
  while not bot.is_closed():
    now = datetime.now(timezone.utc)
    if now.hour == 10 and now.minute == 0:
      await run_broadcast("10:00 AM UTC Automatic Timer")
      await asyncio.sleep(61)
    await asyncio.sleep(30)


@bot.event
async def on_message(message):
  if message.author.id != bot.user.id:
    return

  content = message.content.strip()
  lower_content = content.lower()

  if lower_content == "hey jarvis":
    try:
      await message.edit(content="Hello master")
    except Exception:
      await message.channel.send("Hello master")
    return

  if lower_content == "jarvis help":
    help_text = (
        "🤖 **Jarvis Command Menu (Python)**\n• `hey jarvis` — Greets you.\n•"
        " `jarvis help` — Shows this help menu.\n• `jarvis start` — Triggers"
        " the morning DM broadcast manually.\n• `jarvis block <user_id>` — Adds"
        " a user to the blacklist.\n• `jarvis add <user_id>` — Forces a user"
        " to get the message.\n• `jarvis message <text>` — Changes the"
        " broadcast text message.\n• `jarvis status` — Displays statistics."
    )
    try:
      await message.edit(content=help_text)
    except Exception:
      await message.channel.send(help_text)
    return

  if lower_content == "jarvis start":
    try:
      await message.delete()
    except Exception:
      pass
    await message.channel.send("🚀 Starting broadcast...")
    await run_broadcast("Manual Command")
    return

  if lower_content.startswith("jarvis block "):
    try:
      target_id = int(content.split(" ")[2])
      if target_id not in blocked_user_ids:
        blocked_user_ids.append(target_id)
        await message.edit(content=f"✅ Successfully blocked user ID: `{target_id}`")
    except Exception:
      pass
    return

  if lower_content.startswith("jarvis add "):
    try:
      target_id = int(content.split(" ")[2])
      forced_user_ids.add(target_id)
      await message.edit(
          content=f"✅ Added user ID `{target_id}` to forced whitelist."
      )
    except Exception:
      pass
    return

  if lower_content.startswith("jarvis message "):
    global message_content
    new_text = content[len("jarvis message ") :]
    message_content = new_text
    await message.edit(content=f"✅ Daily message updated to: `{message_content}`")
    return

  if lower_content == "jarvis status":
    status_text = (
        "📊 **Jarvis Status Report**\n• **Current Message:**"
        f" `{message_content}`\n• **Blocked Users Count:**"
        f" `{len(blocked_user_ids)}`\n• **Forced Whitelist Count:**"
        f" `{len(forced_user_ids)}`\n• **Total Broadcast Runs:**"
        f" `{stats['total_runs']}`\n• *Last Run Stats:* Success:"
        f" `{stats['last_success']}` | Skipped: `{stats['last_skipped']}` |"
        f" Failed: `{stats['last_failed']}`"
    )
    try:
      await message.edit(content=status_text)
    except Exception:
      await message.channel.send(status_text)
    return


bot.run(TOKEN)
