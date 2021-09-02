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
cache: dict[int, tuple[str, int]] = {}
bot.cache = cache


async def get_champion_and_rate(
    db: asqlite.Connection, user_id: int
) -> tuple[str, int]:
    if entry := bot.cache.get(user_id):
        return entry

    async with db.cursor() as cursor:
        await cursor.execute(
            'SELECT "champion", "rate" FROM users WHERE "id"=?;', (user_id,)
        )
        row = await cursor.fetchone()

        if row is None:
            champion = random.choice(champs)
            rate = 10
            await cursor.execute(
                'INSERT INTO users ("id", "champion", "rate") VALUES (?, ?, ?);',
                (user_id, champion, 10),
            )
            await db.commit()
        else:
            champion = row[0]
            rate = row[1]

    bot.cache[user_id] = (champion, rate)

    return (champion, rate)


@bot.command()
async def whoami(ctx: commands.Context) -> None:
    """Tells you which champion you will be quoted as."""
    await ctx.send((await get_champion_and_rate(bot.db, ctx.author.id))[0])


@bot.command()
async def whois(ctx: commands.Context, member: discord.Member) -> None:
    """Tells you which champion another user will be quoted as."""
    await ctx.send((await get_champion_and_rate(bot.db, member.id))[0])


@bot.command()
async def champions(ctx: commands.Context) -> None:
    """Lists all available champions."""
    await ctx.send(", ".join(champs))


@bot.command()
async def iam(ctx: commands.Context, *, champion: str) -> None:
    """Sets a champion that you will be quoted as."""
    if champion not in champs:
        await ctx.send("Invalid champion.")
        return

    async with bot.db.cursor() as cursor:
        await cursor.execute(
            'INSERT INTO users ("id", "champion", "rate") VALUES (?, ?, ?) ON CONFLICT("id") DO UPDATE SET "champion"=?;',
            (ctx.author.id, champion, 10, champion),
        )
        await bot.db.commit()

    bot.cache.pop(ctx.author.id, None)

    await ctx.send(f"Done. You are now {champion}.")


@bot.command()
async def setrate(ctx: commands.Context, rate: int) -> None:
    """Sets your quote rate in percent."""
    if not 0 <= rate <= 100:
        await ctx.send("Rate must be between 0 and 100.")
        return

    async with bot.db.cursor() as cursor:
        await cursor.execute(
            'INSERT INTO users ("id", "champion", "rate") VALUES (?, ?, ?) ON CONFLICT("id") DO UPDATE SET "rate"=?;',
            (ctx.author.id, random.choice(champs), rate, rate),
        )
        await bot.db.commit()

    bot.cache.pop(ctx.author.id, None)

    await ctx.send(f"Done. Your quote rate is now {rate}%.")


@bot.event
async def on_message(msg: discord.Message) -> None:
    if msg.author.bot or msg.channel.id in config["ignore"] or bot.db is None:
        return

    (champion, rate) = await get_champion_and_rate(bot.db, msg.author.id)

    if bot.user in msg.mentions or random.randint(1, 101) <= rate:
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
                'CREATE TABLE IF NOT EXISTS users ("id" BIGINT PRIMARY KEY NOT NULL, "champion" STRING, "rate" INTEGER DEFAULT 10);'
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
