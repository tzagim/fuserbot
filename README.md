# fuserbot
Sending messages from group to group in Telegram using a user and not a bot

## If you want to send messages through a bot, use: [tzbot](https://github.com/tzagim/tzbot)

# installation
You must install telethon and asyncio to use this script
```
$ sudo apt install python3-telethon python3-asyncio
```
OR
```
$ python3 -m pip install telethon asyncio
```

# how to use
+ First, to get the required parameters, go to [telogin](https://github.com/tzagim/telogin)
+ Rename the created file to `fuserbot_config.json`. (it should show in the format of `example_fuserbot_config.json`).
+ Create the file `chats.json` according to the format found in `example_chats.json`
+ Download `fuserbot.py`
+ Run the script:
```
$ python3 fuserbot.py
```
