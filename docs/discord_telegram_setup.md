## Telegram Notification (Optional)
if you want to set-up a Telegram notification system please follow these steps:
1. Create Telegram bot using [@BotFather](https://t.me/BotFather). Note the `API token` generated in the BotFather chat- you'll need it later.
2. Get your `Telegram userid` from [@userinfobot](https://t.me/userinfobot) or alternatively [@MissRose_bot](https://t.me/MissRose_bot)
3. Re-run `setup.py` with two new arguments, like so: `python setup.py --telegram_api_token --telegram_userid <your_userid>`
	- `telegram_api_token` is the token generated from step 1.
	- `telegram_userid` is your userid from step 2

## Discord Notification (Optional)
if you want to setup a Discord notification system please follow these steps:
1. Create a new server, or skip this step if you want to use an existing server you have admin access to
	- Optional: Create a new channel dedicated to summary messages
2. Click the settings gear on the right side of the desired channel > integrations > Webhooks > New Webhook > Copy Webhook URL
	- The name is irrelevant beyond having a quick way of telling what the webhook was created for in discord.
3. Re-run `setup.py` with the discord argument, like so: `python setup.py --discord-webhook-url <your webhook URL copied earlier>`
4. To enable reporting, run BingRewards.py with the `-di` flag. Example: `python BingRewards.py -di`
