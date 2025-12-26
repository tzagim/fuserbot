# fuserbot
Sending messages from one Telegram group to another using a user account instead of a bot is possible. The main difference between a user and a bot is that bots have stricter limitations.

**If you want to send messages through a bot, use: [tzbot](https://github.com/tzagim/tzbot)**

## installation
You must install telethon to use this script
```
$ sudo apt install python3-telethon
```
OR
```
$ python3 -m pip install telethon
```

## how to use
+ First, to get the required parameters, to get them go to [telogin](https://github.com/tzagim/telogin)
+ Rename the generated file to `fuserbot_config.json`. (It should be in the format of `example_fuserbot_config.json`).
+ Create the file `chats.json` according to the format found in `example_chats.json`
+ Download `fuserbot.py`
+ Run the script:
```
$ python3 fuserbot.py
```
