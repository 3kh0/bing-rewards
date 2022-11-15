An automated solution using Python and Selenium for earning daily Microsoft Rewards points in all categories including web, mobile, and offers.


Please note: 
- only `USA` website guaranteed to be supported
- multiple accounts NOT supported

## Getting Started (Local set-up)
Note: If using Docker, feel free to skip directly to that section.

1. Download [Chrome](https://www.google.com/chrome/) or [Edge](https://www.microsoft.com/edge)
2. Install [Python3](https://www.python.org/downloads/)
3. Install requirements.txt file included in the repo: `pip install -r BingRewards/requirements.txt`.
4. Create/update config file by running `python BingRewards/setup.py` .
	 -  **Please note**: Your credentials will be stored as base64 encoded text.
5. You must have signed onto your account using this machine before. Open Chrome or Edge and visit https://login.live.com. The site may ask to send you a verification email or text.
6. Run `python BingRewards/BingRewards.py` to start earning points. 
	- You may need to add `-nsb` flag if running on Linux 
8. Occasionally, update to the latest code by running `./bing-rewards-master/update.sh`
9. Optional alerting: You can receive alerting for the following services, instructions below for each service.
	- Telegram
	- Discord
	- Google Sheets

### Command Line Arguments
There are a growing number of command line argument options. Here are a few to note:
- `-r` or `--remaining`: remaining tasks - this is the *default* option
- `-nhl` or `--no-headless`: Don't run in headless mode. This is a non-default option.
- `-nsb` or `--no-sandbox`: Run browser in [no-sandbox mode](https://unix.stackexchange.com/a/68951). Useful for *Linux*. This is a non-default option.

To see remaining argument options, please run:
```sh
python BingRewards.py -h
```

#### Examples
The following `python BingRewards.py` 
actually translates to `python BingRewards.py -r -hl -d chrome`, i.e run the remaining searches in chrome headless mode.

Here's an example of running non-default arguments
`python BingRewards.py -w -nhl -e my_email@gmail.com -p`, i.e run web searches in non-headless mode with specified email, the password will be prompted for separately.

## Docker Container Set-up (Optional)

Docker makes it easy for you to run any program, including this one, regardless of your environment. You just need to [install docker](https://docs.docker.com/get-docker/) on your machine. 

Please note that not all features are supported using Docker, i.e Telegram.

Once docker is installed, follow these instructions to set-up the BingRewards container:

1. In terminal, run `docker pull killerherts/bing-rewards:latest`
2. Set-up the config with either option 1 or 2 
	 1. Option 1, run setup.py within the container: `docker run -t -d --name bing-rewards killerherts/bing-rewards:latest python setup.py -e <your_email> -p <password>`  You must include your password as there will be no user prompt with -t -d flags.
	 2. Option 2: Pass your config directly into the container: `docker run -t -d -v <absolute-path-to-config-directory>:/bing-rewards/BingRewards/config --name bing-rewards killerherts/bing-rewards:latest`. Note, this option assumes you have a set-up a local copy of this project on your machine.
3. To run BingRewards, you have a variety of options:
	1. Wait for the scheduled cron job to run (every 8 hours)
	2. Execute the python script manually: `docker exec bing-rewards python BingRewards.py -nsb`
3. If for any reason you want to enter the container then run: `docker exec -it bing-rewards /bin/bash`

#### Container Notes: 
1. You may override default environment variables, by adding the following flags in the `docker run` command:
	1. Set a preferred bot run schedule with 
	`-e SCH=<cronexpression>` Default : `0 */8 * * *`
	2. Set a preferred timezone with 
	`-e TZ=<timezone>` Default: `America/New_York`
	3. Set a preferred update schedule with 
	`-e UPDATE=<cronexpression>` Default : `0 0 /1 * *`
4. Logs can be mounted to host file system by using the following with docker run
 `-v <absolute-path-to-logs-directory>:/bing-rewards/BingRewards/logs`
5. Images will be rebuilt daily at 12:26 PM UTC this will update chromium and other image dependencies. If your having issues with the container update it with the following [instructions](https://stackoverflow.com/a/26833005)
6. If you would like to use docker compose a sample configuration can be found [here](https://github.com/jjjchens235/bing-rewards/blob/master/compose.yaml)

## Scheduling (Optional)
You may want to use your operating system's scheduler to run this program automatically. The script will run completely in the background and should NOT interfere with your daily routine.

#### Windows (task scheduler)
1. Open *Task Scheduler* and click *Create Task*.
2. Choose *Run whether user is logged on or not* under *Security options* and check the box at the bottom that says *Hidden*.
3. Add a new trigger, either *On workstation unlock* for your specific username or *On a schedule* daily depending on what you want.
4. When adding the action, point the program to *__python.exe__* (most likely located in *__C:/Program Files__*) and add the argument line `BingRewards/BingRewards.py`. In the *Start in* box, place the absolute path to where you've cloned this repository.
5. It's also recommended to select the option to only execute when there is a network connection available under the *Conditions* tab.

#### Mac / Linux / Docker (crontab)

1. Open up the terminal and go to your home directory `cd ~`
2. Type `crontab -e`.
3. Now append the following line with the correct path: `0 9 * * * /absolute/path/to/python /absolute/path/to/BingRewards/BingRewards.py`. The second digit, in this case the 9, is the hour (0-23) in your local timezone when the program will be run. Also note the default text editor for crontab is VIM so you'll need to hit `i` before editing text, and `esc` to go back to vim mode whereupon you can type in `:wq` which will write the changes and quit.
4. An example cronjob using an Anaconda Python build that runs daily at 9am: `0 9 * * * /Applications/anaconda/bin/python ~/Programming/Python/bing-rewards-master/BingRewards/BingRewards.py`
5. Note that cronjobs are not run if your computer is sleeping. To wake your computer at a scheduled time follow the instructions in this [link](https://alvinalexander.com/mac-os-x/mac-wake-up-schedule-automatic-time-sleep).

## Telegram Notification (Optional)
if you want to setup a Telegram notification system please follow these steps:
1. Create Telegram bot using [@BotFather](https://t.me/BotFather). Note the API token generated in the BotFather chat- you'll need it later.
2. Get your Telegram userid from [@userinfobot](https://t.me/userinfobot) or alternatively [@MissRose_bot](https://t.me/MissRose_bot)
3. Re-run `setup.py` with two new arguments, like so: `python setup.py --telegram_api_token --telegram_userid <your_userid>`
	- `telegram_api_token` is the token generated from step 1. You can enter the token value separately in a secure prompt.
	- `telegram_userid` is your userid from step 2

## Discord Notification (Optional)
if you want to setup a Discord notification system please follow these steps:
1. Create a new server, or skip this step if you want to use an existing server you have admin access to
	- Optional: Create a new channel dedicated to summary messages
2. Click the settings gear on the right side of the desired channel > integrations > Webhooks > New Webhook > Copy Webhook URL
	- The name is irrelevant beyond having a quick way of telling what the webhook was created for in discord.
3. Re-run `setup.py` with the discord argument, like so: `python setup.py --discord-webhook-url <your webhook URL copied earlier>`
4. To enable reporting, run BingRewards.py with the `-di` flag. Example: `python BingRewards.py -di`

## Google Sheets API Instructions (Optional)
Before proceeding, please note:
- that the process is somewhat involved, it should take around 30 minutes to get everything set-up
- Each week, you will be forced to **manually** reauthenticate in order to generate a new token.

If you would still like to proceed, here are the steps:

1. Go to the `Google Sheets API` [page](https://console.cloud.google.com/apis/library/sheets.googleapis.com?authuser=2).
	- Click `Enable`. After a few moments, you will be taken to a project page
	- On the left hand side are some tabs, click `Credentials`.
	- Click `+ Create Credentials` -> `OAuth Client Id`
2. You will first need to configure consent screen, here
	-  Click `CONFIGURE CONSENT SCREEN`
		- Choose `External`
		- Fill out the required fields
	- Scopes screen: just click `Save and Continue`
	- Test users screen: 
		- add test user email, use the same email as your google account
		- click `Save and Continue`
3. Go back to `Credentials` tab 
	1. Click `+ Create Credentials` -> `OAuth Client Id`
	1. For `Application type` select `Web application`
	1. For `Name` make up a name.
	1. (Optional): Under section `Authorized redirect URIs`, click `Add URI`. Add the following 2 URI's: `https://localhost/` and `http://localhost/`
	1. Click `CREATE`
	1. A popup will say `OAuth client created` with your credentials, at the bottom click `DOWNLOAD JSON`
4. Update json filename and path
	- move the json file to this path: `bing-rewards-master/BingRewards/config`
	- rename the file to: `google_sheets_credentials.json`. 
	- For the two steps above, via cmd line, it would look something like this:
```sh
cd bing-rewards-master/BingRewards/config/
#move downloaded file to correct dir and rename file
mv ~/Downloads/client_secret_xxx.json ./google_sheets_credentials.json
```
5. Lastly, this program needs access to the `sheet_id` and `tab_name` 
	- Get the `sheet_id` by following these [instructions](https://stackoverflow.com/a/36062068).
	- The `tab_name` is simply the name of the tab, i.e `Sheet1`
	- Re-run setup.py to update the config file:
```py
python setup.py --google_sheets_sheet_id <your_sheet_id> --google_sheets_tab_name <your_tab_name>
```
6. To summarize, the end result of the above is the following:
	- In the `config/` directory, there is a `google_sheets_credentials.json` which was downloaded from google credentials page.
	- `config/config.json` was updated via `setup.py` and now contains the following:
		- sheet_id
		- tab_name

## Additional Login Security Options
Microsoft offers these additional security options:
- Passwordless account: No password, tap the correct number from your authenticator app
- Two-step verification: You'll have to enter a security code that is sent to you via email or authenticator app

Currently `only passwordless is supported` and it must be done through the `Microsoft Authenticator` app.

Each time you log-in, a code will be printed out in the `command line console`, and you will need to select it in Authenticator. You will have to do this an additional time when you do the mobile search.

## Multiple accounts
Multiple accounts are not supported currently,
 and there are no plans to add this feature. This is the most common question/request, but the reason for this is because it goes against the original author's intention and I want to honor that.

## Acknowledgment
- The original author took down the code from their GitHub back in July 2018. The author gave me permission to re-upload and maintain, but wishes to stay anonymous. I will continue to maintain until this page says otherwise.
- UK quiz updates by `chris987789`
- 2FA code by `revolutionisme`
- Telegram notifications by `hoseininjast`
- Punch card, dashboard json, This or That perfect score, and more based on `Charles Bel's` wonderful [repo](https://github.com/charlesbel/Microsoft-Rewards-Farmer).
- Microsoft Edge support by `Summon528`
