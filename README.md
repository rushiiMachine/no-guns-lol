# no-guns-lol

discord selfbot to ban anyone with guns.lol on their profile

Most people with a profile on https://guns.lol listed on their Discord profile have never
failed to be the most arrogant, edgy, and all around awful people to be around. This project is a
selfbot (since regular bots cannot access user profiles) to automatically ban anyone joining
with a link to that website.

## Running

You should not use this on an account you value in any sort of way. Create an alt, and use that instead.
There is the possibility of the account being banned or flagged for phone verification at any time.

Run (docker):

```shell
docker run \
  -e TOKEN=<TOKEN> \
  -e OWNER=0123 \
  -e SCAN_GUILDS=0123,4567 \
  -e USERS_WHITELIST=0123,4567 \
  ghcr.io/rushiiMachine/no-guns-lol
```

Environment variables:

| name              | type        | description                                                                                                                                                            |
|-------------------|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `TOKEN`           | string      | A Discord user token. You can obtain this by opening devtools and extracting the `Authorization` header (removing the `Bearer ` prefix) from an authenticated request. |
| `OWNER`           | Snowflake   | A single user id that is allowed the `.scan` command.                                                                                                                  |
| `SCAN_GUILDS`     | Snowflake[] | List of server ids separated by commas. This is used to select the servers to automatically scan.                                                                      |
| `USERS_WHITELIST` | Snowflake[] | List of user ids separated by commas. These users will be skipped during scans.                                                                                        |

## Usage

The user account supplied to this bot has to have ban permissions in the target servers (that ones provided
by the `SCAN_GUILDS` environment variable). No scans will be performed on joining or existing members until
permissions to ban members has been given.

Due to a limitation of the Discord gateway, there is no way to detect when certain profile elements change, such
as the bio. As such, this bot provides a way to manually scan members through the use of the `.scan` command. By
either logging into the account yourself, or setting the `OWNER` environment variable, and sending the command in a
server that the account has permissions in, a full member scan will be started. Every single member will be fetched
one by one, 1/sec (due to Discord ratelimits). Additionally, there may be an additional Cloudflare ratelimits imposed
on fetching profiles, which will significantly slow down the process by more than 86x. Without the Cloudflare
ratelimits, scanning a 100k member server will take roughly 28 hours to complete.

Due to how slow scanning every member is, I recommend only doing this once and letting the rest of the scanning be
handled on-demand. All new members will be scanned, as well as every time a member sends a message in a channel the
account has access to. Members scanned as a result of sending a message will be cached for 24h to prevent re-fetching.