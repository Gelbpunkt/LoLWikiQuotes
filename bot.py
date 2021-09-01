import asyncio
import collections
import json
import random
from typing import Generator, Iterable

import aiosqlite
import discord
from discord.ext import commands

with open("quotes_list_export.json", "r") as f:
    quotes = json.load(f)

with open("config.json", "r") as f:
    config = json.load(f)


def flatten(l: Iterable) -> Generator:
    for el in l:
        if isinstance(el, collections.abc.Iterable) and not isinstance(el, str):
            for sub in flatten(el):
                yield sub
        else:
            yield el


champs = list(quotes.keys())

bot = commands.Bot(command_prefix="!")


async def get_champion(db: aiosqlite.Connection, user_id: int) -> str:
    cursor = await db.execute('SELECT "champion" FROM users WHERE "id"=?;', (user_id,))
    row = await cursor.fetchone()

    if row is None:
        champion = random.choice(champs)
        await cursor.close()
        await db.execute(
            'INSERT INTO users ("id", "champion") VALUES (?, ?);', (user_id, champion)
        )
        await db.commit()
    else:
        champion = row[0]
        await cursor.close()

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

    await bot.db.execute(
        'INSERT INTO users ("id", "champion") VALUES (?, ?) ON CONFLICT("id") DO UPDATE SET "champion"=?;',
        (ctx.author.id, champion, champion),
    )
    await bot.db.commit()
    await ctx.send(f"Done. You are now {champion}.")


@bot.event
async def on_message(msg: discord.Message) -> None:
    if msg.author.bot or msg.channel.id in config["ignore"]:
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
        print(f"**{msg.author} ({champion})**: {quote}")

    await bot.process_commands(msg)


async def run() -> None:
    bot.db = await aiosqlite.connect("bot.db")
    bot.webhooks = {}
    await bot.db.execute(
        'CREATE TABLE IF NOT EXISTS users ("id" BIGINT PRIMARY KEY NOT NULL, "champion" STRING);'
    )
    await bot.db.commit()

    try:
        await bot.start(config["token"])
    except KeyboardInterrupt:
        pass
    finally:
        await bot.db.close()


asyncio.run(run())
