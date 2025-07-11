import os

from discord import Member, MemberProfile, Message, Client

TOKEN = os.getenv("DISCORD_TOKEN")
GUILDS_RAW = os.getenv("GUILDS")

if not TOKEN:
    raise Exception("Missing DISCORD_TOKEN environment variable)")
if not GUILDS_RAW:
    raise Exception("Missing GUILDS environment variable")

GUILDS: list[int] = [int(guild_id) for guild_id in GUILDS_RAW.split(",")]

client = Client(guild_subscriptions=False)


@client.event
async def on_ready(self: Client):
    print(f'Logged in as {self.user.name}#{self.user.discriminator} ({self.user.id})')
    for guild_id in GUILDS:
        guild = await self.fetch_guild(guild_id)
        await guild.subscribe(typing=True, member_updates=True, activities=False, threads=False)


@client.event
async def on_member_join(_self, member: Member):
    print(f'New member joined: {member.name} ({member.id})')
    await handle_user(member=await member.profile())


@client.event
async def on_member_update(_self, _before: Member, after: Member):
    await handle_user(member=await after.profile())


async def handle_user(member: MemberProfile):
    if "https://guns.lol/" in member.guild_bio or "https://guns.lol/" in member.bio:
        print(f"Banning {member.name} ({member.id})")
        await member.ban(reason="guns.lol in bio")


@client.event
async def on_message(_self, message: Message):
    if message.content == '$$$ping':
        await message.reply('pong', mention_author=False)


if __name__ == '__main__':
    client.run(TOKEN)
