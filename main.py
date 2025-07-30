import logging
import os

import coloredlogs

from no_guns_lol import NoGunsLolClient, start_cache_auto_expire


def main():
    token = os.getenv("TOKEN")
    guilds_raw = os.getenv("SCAN_GUILDS")
    users_whitelist = os.getenv("WHITELIST_USERS")
    owner = os.getenv("OWNER")
    debug = len(os.getenv("DEBUG", "")) > 0

    guilds = []
    whitelist_users = []

    coloredlogs.install(
        isatty=True,
        level=logging.DEBUG if debug else logging.INFO,
        logger=logging.root,
        fmt="[{asctime}] [{levelname:<7}] {name}: {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _log = logging.getLogger(__name__)

    if not token:
        raise Exception("Missing TOKEN environment variable!")

    if not guilds_raw:
        _log.warning("The SCAN_GUILDS environment variable is missing; not subscribing to any guilds! "
                     "This means that no users from any guild will be scanned!")
    else:
        guilds = [int(gid) for gid in guilds_raw.split(",")]

    if not owner:
        _log.warning("The OWNER environment variable is not set! This selfbot will only respond to commands "
                     "sent from it's own account! Set it to a user id in order to make it respond to your main account!")

    if users_whitelist:
        whitelist_users = [int(uid) for uid in users_whitelist.split(",")]
        _log.info(f"Users exempted from bans: {whitelist_users}")

    client = NoGunsLolClient(
        target_guilds=guilds,
        whitelist_users=whitelist_users,
        owner_uid=int(owner) if owner else None,
    )

    start_cache_auto_expire()
    client.run(token, log_handler=None)


if __name__ == '__main__':
    main()
