import logging
import math
import threading
import time
from datetime import timedelta
from random import randint
from time import sleep
from typing import Optional

from cachetools import TTLCache
from discord import Member, Message, Client, Guild, HTTPException, NotFound, InvalidData

_log = logging.getLogger(__name__)
_checkedUsers = TTLCache(maxsize=math.inf, ttl=timedelta(days=1).total_seconds())


def start_cache_auto_expire():
    def loop():
        while True:
            sleep(timedelta(days=1).total_seconds())
            _log.debug("Clearing expired checked users cache")
            _checkedUsers.expire()  # Remove expired entries

    threading.Thread(target=loop, daemon=True).start()


async def handle_member(member: Member) -> bool:
    if member.bot: return False
    if member.id in _checkedUsers: return False

    try:
        _log.debug(f"Fetching profile for {member.name} ({member.id})")
        profile = await member.profile(
            with_mutual_guilds=False,
            with_mutual_friends=False,
            with_mutual_friends_count=False)
    except HTTPException as e:
        _log.error(f"Failed to fetch profile for {member.id}", e)
        return False
    except (NotFound, InvalidData):
        _checkedUsers[member.id] = True
        return False

    if ((profile.bio and "https://guns.lol/" in profile.bio) or
            (profile.guild_bio and "https://guns.lol/" in profile.guild_bio)):
        try:
            _log.info(f"Banning {profile.name} ({profile.id})")
            await profile.ban(reason="guns.lol in bio")
            return True
        except Exception as e:
            _log.warning(f"Failed to ban {profile.name} ({profile.id})", e)
    else:
        _checkedUsers[member.id] = True

    return False


class NoGunsLolClient(Client):
    def __init__(self,
                 target_guilds: list[int],
                 whitelist_users: Optional[list[int]] = None,
                 owner_uid: Optional[int] = None,
                 ):
        super(NoGunsLolClient, self).__init__(guild_subscriptions=False, max_messages=None)
        self._target_guilds: set[int] = set(target_guilds)
        self._whitelist_users: set[int] = set(whitelist_users or [])
        self._owner_uid: Optional[int] = owner_uid

    async def handle_scan(self, message: Message):
        if not message.guild.me.guild_permissions.ban_members:
            await message.reply("This account does not have permissions to ban members of this server!")
            return

        _log.info(f"Scanning guild {message.guild.name} ({message.guild.id}), "
                  f"requested by {message.author}({message.author.id})")

        members = await message.guild.fetch_members(cache=False)
        member_count = len(members)

        time_start = time.time()
        time_estimate = timedelta(seconds=int(member_count * 1.01))
        status_message = await message.reply(
            f"Scanning {member_count} members, estimated time: {chop_timedelta(time_estimate)}")

        members_processed = 0
        members_banned = 0

        async def update_status_message():
            time_elapsed = chop_timedelta(timedelta(seconds=time.time() - time_start))
            processed_percent = members_processed / member_count * 100
            await status_message.edit(content=
                                      f"Scanning {member_count} members, estimated time: {time_estimate}\n\n"
                                      f"*Elapsed time: {time_elapsed}*, processed members: {members_processed} "
                                      f"({processed_percent:.1f}%)")

        for member in [m for m in members if m.id not in self._whitelist_users]:
            sleep(1.01)
            members_banned += await handle_member(member)
            members_processed += 1

            # Update status message around 1/min
            if members_processed % 60 == 1:
                await update_status_message()

        await update_status_message()
        await message.reply(f"Finished scanning, banned {members_banned} members!", mention_author=True)

    async def handle_server_join(self, guild: Guild):
        if guild.id in self._target_guilds:
            _log.debug(f"Subscribing to guild {guild.name} ({guild.id})")
            await guild.subscribe(typing=True, activities=False, threads=False, member_updates=True)

    # Events

    async def on_ready(self):
        _log.info(f'Logged in as {self.user.name}#{self.user.discriminator} ({self.user.id})')

        for guild_id in self._target_guilds:
            guild = self.get_guild(guild_id)
            if not guild:
                _log.warning(
                    f"Target guild {guild_id} was not found! No scans can be performed for this server until this account has joined it!")
                continue

            if not guild.me.guild_permissions.ban_members:
                _log.warning(
                    f"This account does not have permissions to ban members in the target guild {guild.name} ({guild.id})! "
                    f"No scans will be performed in this server until this account has been given permissions the necessary permissions!")

            _log.debug(f"Subscribing to guild {guild.name} ({guild.id})")
            await guild.subscribe(typing=True, activities=False, threads=False, member_updates=True)

    async def on_guild_join(self, guild: Guild):
        await self.handle_server_join(guild)

    async def on_guild_available(self, guild: Guild):
        await self.handle_server_join(guild)

    async def on_member_join(self, member: Member):
        if (member.guild.id in self._target_guilds and
                member.guild.me.guild_permissions.ban_members and
                member.id not in self._whitelist_users):
            sleep(randint(1, 5))  # Random jitter
            await handle_member(member)

    async def on_message(self, message: Message):
        if message.author.id in [self.user.id, self._owner_uid]:
            if message.guild and message.content == ".scan":
                await self.handle_scan(message)
            return
        elif (message.guild and
              message.guild.me.guild_permissions.ban_members and
              message.guild.id in self._target_guilds):
            await handle_member(message.author)


def chop_timedelta(delta: timedelta) -> timedelta:
    return timedelta(seconds=math.ceil(delta.total_seconds()))


__all__ = (
    NoGunsLolClient,
    start_cache_auto_expire,
)
