An automated solution using Python and Selenium for earning daily Microsoft Rewards points in all categories including web, mobile, and offers.

Please note: 
- only US website guaranteed to be supported
- multiple accounts NOT supported

## Getting Started
1. Download [Chrome](https://www.google.com/chrome/)
2. Install [Python3](https://www.python.org/downloads/)
3. Install `requirements.txt` file included in the repo: `pip install -r BingRewards/requirements.txt`.
4. If you want notifications via Telegram, follow the steps [below](https://github.com/jjjchens235/bing-rewards#telegram-notification), else continue ahead
5. Create config file by running `python setup.py`. If you need to update your email or password, re-run this. 
	- Please note your email and password will be saved essentially as plain text (base64 encoded). If you prefer, leave the setup arguments blank and use the --email and --password command line arguments instead.
6. You must have signed onto your account using this machine before. Open Chrome and visit https://login.live.com. The site may ask to send you a verification email or text.
7. And you're all set! Run `python BingRewards/BingRewards.py` to start earning points.

## Command Line Arguments
#### Search Arguments
* `-r` or `--remaining`: remaining tasks - this is the *default* option
* `-w` or `--web`: web search
* `-m` or `--mobile`: mobile search
* `-b` or `--both`: both searches (web search and mobile search)
* `-o` or `--offers`: daily offers
* `-a` or `--all`: all tasks (web search, mobile search and daily offers)

#### Additional Optional Arguments
* Email/Password
	* `-e` or `--email`: email to use, supersedes the config email
	* `-p` or `--password`: the email password to use. Use -p with no argument to trigger a secure pw prompt
* Headless
	* `-hl` or `--headless`: Run in [headless](https://developers.google.com/web/updates/2017/06/headless-karma-mocha-chai) mode- this is the *default*
	* `-nhl` or `--no-headless`: Don't run in headless mode
* Cookies
	* `-nc` or `--no-cookies`: Browser does not save cookies- this has been updated to be the *default* due to a few people reporting issues with the cookies option.
	* `-c` or `--cookies`: Run browser with cookies to preserve username and pw each session.
* Telegram
	* `-t` or `--telegram`: Send notifications to telegram (more instructions below). This is the *default*, but will only work if telegram credentials were entered during setup
	* `-nt` or `--no-telegram`: Do not send notifications to telegram

#### Examples
The following `python BingRewards.py` 
actually translates to `python BingRewards.py -r -hl`, i.e run the remaining searches in headless mode.

Here's an example of running non-default arguments
`python BingRewards.py -w -nhl -e my_email@gmail.com -p`, i.e run web searches in non-headless mode with specified email, password will be prompted for separately.

## Scheduling (Optional)
You may want to use your operating system's scheduler to run this program automatically. The script will run completely in the background and should NOT interfere with your daily routine.

#### Windows (task scheduler)
1. Open *Task Scheduler* and click *Create Task*.
2. Choose *Run whether user is logged on or not* under *Security options* and check the box at the bottom that says *Hidden*.
3. Add a new trigger, either *On workstation unlock* for your specific username or *On a schedule* daily depending on what you want.
4. When adding the action, point the program to *__python.exe__* (most likely located in *__C:/Program Files__*) and add the argument line `BingRewards/BingRewards.py`. In the *Start in* box, place the absolute path to where you've cloned this repository.
5. It's also recommended to select the option to only execute when there is a network connection available under the *Conditions* tab.


#### Mac / Linux (crontab)


1. Open up the terminal and go to your home directory `cd ~`
2. Type `crontab -e`.
3. Now append the following line with the correct path: `0 9 * * * /absolute/path/to/python /absolute/path/to/BingRewards/BingRewards.py`. The second digit, in this case the 9, is the hour (0-23) in your local timezone when the program will be run. Also note the default text editor for crontab is VIM so you'll need to hit `i` before editing text, and `esc` to go back to vim mode whereupon you can type in `:wq` which will write the changes and quit.
4. An example cronjob using an Anaconda Python build that runs daily at 9am: `0 9 * * * /Applications/anaconda/bin/python ~/Programming/Python/bing-rewards-master/BingRewards/BingRewards.py`
5. Note that cronjobs are not run if your computer is sleeping. To wake your computer at a scheduled time follow the instructions in this [link](https://alvinalexander.com/mac-os-x/mac-wake-up-schedule-automatic-time-sleep).

## Two-factor Authentication
2FA is supported, but only through `Microsoft Authenticator`.

Each time you log-in, a code will be printed out in the console, and you will need to select it in Authenticator. You will have to do this an additional time when you do the mobile search.

## Telegram Notification
if you want to setup telegram notification system please follow these steps:
1. Create bot in telegram from [@BotFather](https://t.me/BotFather). File away the API token generated in the BotFather chat- you'll need it later.
2. Get your telegram userid from [@userinfobot](https://t.me/userinfobot) or alternatively [@MissRose_bot](https://t.me/MissRose_bot)
3. Run setup `python setup.py` and enter 
	- your token generated from step 1
	- your userid from step 2

## Multiple accounts
Multiple accounts is not supported currently, and there is no plans to add this feature. This is the most common question/request, but the reason for this is because it goes against the original author's intention and I want to honor that.

## Acknowledgement
- Original author took down the code from their GitHub back in July 2018. Author gave me permission to re-upload and maintain, but wishes to stay anonymous. I will continue to maintain until this page says otherwise.
- UK quiz updates written and tested by `chris987789`
- 2FA code written by `revolutionisme`
- Telegram notifications written by `hosein-hub`
