import json
import logging
import random

import asqlite
import discord
import uvloop
from discord.ext import commands

uvloop.install()

logging.basicConfig(level=logging.INFO)

with open("quotes_list_export.json", "r") as f:
    quotes = json.load(f)

with open("config.json", "r") as f:
    config = json.load(f)

champs = list(quotes.keys())

bot = commands.Bot(command_prefix="!")


async def get_champion(db: asqlite.Connection, user_id: int) -> str:
    async with db.cursor() as cursor:
        await cursor.execute('SELECT "champion" FROM users WHERE "id"=?;', (user_id,))
        row = await cursor.fetchone()

        if row is None:
            champion = random.choice(champs)
            await cursor.execute(
                'INSERT INTO users ("id", "champion") VALUES (?, ?);',
                (user_id, champion),
            )
            await db.commit()
        else:
            champion = row[0]

    return champion


@bot.command()
async def whoami(ctx: commands.Context) -> None:
    """Tells you which champion you will be quoted as."""
    await ctx.send(await get_champion(bot.db, ctx.author.id))


@bot.command()
async def iam(ctx: commands.Context, *, champion: str) -> None:
    """Sets a champion that you will be quoted as."""
    if champion not in champs:
        await ctx.send("Invalid champion.")
        return

    async with bot.db.cursor() as cursor:
        await cursor.execute(
            'INSERT INTO users ("id", "champion") VALUES (?, ?) ON CONFLICT("id") DO UPDATE SET "champion"=?;',
            (ctx.author.id, champion, champion),
        )
        await bot.db.commit()

    await ctx.send(f"Done. You are now {champion}.")


@bot.event
async def on_message(msg: discord.Message) -> None:
    if msg.author.bot or msg.channel.id in config["ignore"] or bot.db is None:
        return

    if bot.user in msg.mentions or random.randint(1, 10) == 1:
        webhook = bot.webhooks.get(msg.channel.id)
        if webhook is None:
            webhooks = await msg.channel.webhooks()
            if not webhooks:
                webhook = await msg.channel.create_webhook(name="Jazzy")
            else:
                webhook = discord.utils.find(
                    lambda hook: hook.token is not None, webhooks
                )
                if webhook is None:
                    webhook = await msg.channel.create_webhook(name="Jazzy")
            bot.webhooks[msg.channel.id] = webhook

        champion = await get_champion(bot.db, msg.author.id)
        quote = random.choice(quotes[champion]["quotes"])
        await webhook.send(
            quote, username=msg.author.display_name, avatar_url=quotes[champion]["icon"]
        )

    await bot.process_commands(msg)


@bot.event
async def on_ready():
    if bot.db is None:
        bot.db = await asqlite.connect("bot.db")
        async with bot.db.cursor() as cursor:
            await cursor.execute(
                'CREATE TABLE IF NOT EXISTS users ("id" BIGINT PRIMARY KEY NOT NULL, "champion" STRING);'
            )
            await bot.db.commit()
        logging.info("Database initialized")


bot.db = None
bot.webhooks = {}

try:
    bot.run(config["token"])
except KeyboardInterrupt:
    pass
finally:
    bot.db.get_connection().close()
