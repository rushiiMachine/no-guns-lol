# no-guns-lol

discord selfbot to ban anyone with guns.lol on their profile

Most people with a profile on https://guns.lol listed on their Discord profile have never
failed to be the most arrogant, edgy, and all around awful people to be around. This project is a
selfbot (since regular bots cannot access user profiles) to automatically ban anyone joining
with a link to that website.

## Usage

```shell
docker run \
  -e DISCORD_TOKEN=<TOKEN> \
  -e GUILDS=0123,4567 \
  ghcr.io/rushiiMachine/no-guns-lol
```

You should not use this on an account you value in any sort of way. Create an alt, and use that instead.
There is the possibility of the account being banned or flagged for phone verification at any time.

This system has a limitation where members that have already joined are not able to be
automatically scanned whenever they update their bio. As such, this will have to be done manually,
by logging into the account yourself, and sending a message with `.scan` in the target server.
It will fetch every single member and then fetch their profile one by one, one per second (due to ratelimits).
As such, scanning a 100k member server will take roughly 28 hours to complete.
