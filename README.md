An automated solution using Python and Selenium for earning daily Microsoft Rewards points in all categories including web, mobile, and offers.

Please note: multiple accounts not supported, USA and UK users only.

## Getting Started
1. This solution requires Google Chrome which can be downloaded from https://www.google.com/chrome/browser/desktop/index.html.
2. If you don't already have Python 3 installed, visit https://www.python.org/downloads/.
3. Now install the dependencies using the *__BingRewards/requirements.txt__* file included in the repo: `pip install -r BingRewards/requirements.txt`.
4. Next you'll need to create a configuration file that stores your Microsoft account credentials. Run *__setup.py__* and enter the necessary info. This will create the file *__BingRewards/src/config.py__* for you and can be rerun every time you update your password. Rest assured, __your credentials will NOT be stored in plain text__.
5. __You must have signed onto your account using this machine before__. Open Chrome and visit https://login.live.com. The site may ask to send you a verification email or text.
6. And you're all set! You can now either run *__BingRewards/BingRewards.py__* and follow the on-screen instructions to get started or pass any one of the arguments below to by-pass the intro.

## Arguments
* `-w` or `--web`: web search
* `-m` or `--mobile`: mobile search
* `-b` or `--both`: both tasks (web search and mobile search)
* `-o` or `--offers`: daily offers
* `-a` or `--all`: all tasks (web search, mobile search and daily offers)
* `-r` or `--remaining`: remaining tasks (web search, mobile search or daily offers)

## Scheduling (Optional)
You may want to use your operating system's scheduler to run this program automatically. The script will run completely in the background and should NOT interfere with your daily routine.

### Windows (task scheduler)
1. Open *Task Scheduler* and click *Create Task*.
2. Choose *Run whether user is logged on or not* under *Security options* and check the box at the bottom that says *Hidden*.
3. Add a new trigger, either *On workstation unlock* for your specific username or *On a schedule* daily depending on what you want.
4. When adding the action, point the program to *__python.exe__* (most likely located in *__C:/Program Files__*) and add the argument line `BingRewards/BingRewards.py -r`. In the *Start in* box, place the absolute path to where you've cloned this repository.
5. It's also recommended to select the option to only execute when there is a network connection available under the *Conditions* tab.

### Mac (crontab)
1. Open up the terminal and go to your home directory `cd ~`
2. Type `crontab -e`.
3. Now append the following line with the correct path: `0 9 * * * /absolute/path/to/python /absolute/path/to/BingRewards/BingRewards.py -r`. The second digit, in this case the 9, is the hour (0-23) in your local timezone when the program will be run. Also note the default text editor for crontab is VIM so you'll need to hit `i` before editing text, and `esc` to go back to vim mode whereupon you can type in `:wq` which will write the changes and quit.
4. An example cronjob using an Anaconda Python build that runs daily at 9am: `0 9 * * * /Applications/anaconda/bin/python ~/Programming/Python/bing-rewards-master/BingRewards/BingRewards.py -r`
5. Note that cronjobs are not run if your computer is sleeping. To guarantee that the computer is awake prior to the cronjob, use system preferences to automatically wake the computer up right before the cronjob is set to run. This is very easy to set-up, for more details, follow this link: https://alvinalexander.com/mac-os-x/mac-wake-up-schedule-automatic-time-sleep

## Multiple accounts
Multiple accounts is not supported currently, and there is no plans to add this feature. This is the most common question/request, but the reason for this is because it goes against the original author's intention and I want to honor that.

Caveat: I think a docker container implementation would be a good middle ground solution. Unfortunately, I'm not too familiar with Docker so someone would have to implement it and I would gladly issue a pull request.

## Known Issues (Last Updated Aug 2020)
- The first daily offer shows "failed to complete" on the terminal because the quiz doesn't appear when clicked, but Bing gives the points anyways so it's a non-issue.

## Original Author
Original author took down the code from their GitHub back in July 2018. Author gave me permission to re-upload and maintain, but wishes to stay anonymous. I will continue to maintain until this page says otherwise.
