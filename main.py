import logging
import os
from datetime import timedelta
from time import sleep

from discord import Member, Message, Client, Guild, HTTPException, NotFound, InvalidData

_log = logging.getLogger("no-guns-lol")


async def handle_member(member: Member) -> bool:
    if member.bot: return False

    profile = None
    try:
        _log.debug(f"Fetching profile for {member.name} ({member.id})")
        profile = await member.profile(
            with_mutual_guilds=False,
            with_mutual_friends=False,
            with_mutual_friends_count=False)
    except HTTPException as e:
        _log.error(f"Failed to fetch profile for {member.id}", e)
    except (NotFound, InvalidData):
        pass

    if ((profile.bio and "https://guns.lol/" in profile.bio) or
            (profile.guild_bio and "https://guns.lol/" in profile.guild_bio)):
        try:
            _log.info(f"Banning {profile.name} ({profile.id})")
            await profile.ban(reason="guns.lol in bio")
            return True
        except Exception as e:
            _log.warning(f"Failed to ban {profile.name} ({profile.id})", e)

    return False


class NoGunsLolClient(Client):
    def __init__(self, target_guilds: list[int], whitelist_users: list[int]):
        super(NoGunsLolClient, self).__init__(guild_subscriptions=False, max_messages=None)
        self._all_target_guilds: set[int] = set(target_guilds)
        self._available_target_guilds: set[int] = set()
        self._whitelist_users: set[int] = set(whitelist_users)

    # Events

    async def on_ready(self):
        _log.info(f'Logged in as {self.user.name}#{self.user.discriminator} ({self.user.id})')

        guilds = [g for g in (self.get_guild(gid) for gid in self._all_target_guilds) if
                  g and g.me.guild_permissions.ban_members]
        self._available_target_guilds = set([g.id for g in guilds])

        for guild in guilds:
            _log.debug(f"Subscribing to guild {guild.name} ({guild.id})")
            await guild.subscribe(typing=True, activities=False, threads=False, member_updates=True)

    async def on_guild_remove(self, guild: Guild):
        self._available_target_guilds -= guild.id

    async def on_guild_join(self, guild: Guild):
        if guild.id in self._all_target_guilds:
            self._available_target_guilds += guild.id
            _log.debug(f"Subscribing to guild {guild.name} ({guild.id})")
            await guild.subscribe(typing=True, activities=False, threads=False, member_updates=True)

    async def on_member_join(self, member: Member):
        if member.id not in self._whitelist_users:
            profile = await member.profile()
            await handle_member(profile)

    async def on_message(self, message: Message):
        if message.author.id != self.user.id: return

        if message.content == ".scan" and message.guild:
            _log.info(f"Scanning guild {message.guild.name} ({message.guild.id})")
            members = await message.guild.fetch_members(cache=False)

            time_estimate = timedelta(seconds=int(len(members) * 1.01))
            await message.reply(f"Scanning {len(members)} members, estimated time: {time_estimate}")

            members_banned = 0
            for member in [m for m in members if m.id not in self._whitelist_users]:
                sleep(1.01)
                members_banned += await handle_member(member)

            await message.reply(f"Finished scanning, banned {members_banned} members!", mention_author=True)


def main():
    token = os.getenv("DISCORD_TOKEN")
    guilds_raw = os.getenv("GUILDS")
    users_whitelist = os.getenv("WHITELIST_USERS")
    debug = len(os.getenv("DEBUG", "")) > 0

    guilds = []
    whitelist_users = []

    if not token:
        raise Exception("Missing DISCORD_TOKEN environment variable)")

    if not guilds_raw:
        _log.warning("The GUILDS environment variable is missing, not subscribing to any guilds...")
        _log.warning("This means that no new users from any guild will be scanned")
    else:
        guilds = [int(gid) for gid in guilds_raw.split(",")]

    if users_whitelist:
        whitelist_users = [int(uid) for uid in users_whitelist.split(",")]
        _log.info(f"Users exempted from bans: {whitelist_users}")

    client = NoGunsLolClient(
        target_guilds=guilds,
        whitelist_users=whitelist_users)

    client.run(
        token,
        root_logger=True,
        log_level=logging.DEBUG if debug else logging.INFO)


if __name__ == '__main__':
    main()
