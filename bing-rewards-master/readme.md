# Bing Rewards
An automated solution for earning daily Microsoft Rewards points.


## Getting Started
1. This solution requires Google Chrome which can be downloaded from https://www.google.com/chrome/browser/desktop/index.html.
2. If you don't already have Python 3 installed, visit https://www.python.org/downloads/. 
3. Now install the dependencies using the *__BingRewards/requirements.txt__* file included in the repo: `pip install -r BingRewards/requirements.txt`.
4. Next you'll need to create a configuration file that stores your Micrrosoft account credentials. Run *__setup.py__* and enter the necessary info. This will create the file *__BingRewards/src/config.py__* for you and can be rerun every time you update your password. Rest assured, __your credentials will NOT be stored in plain text__.
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
You may want to use your operating system's scheduler to run the script every time you unlock your machine and/or everyday at 12AM PST incase you leave your machine running for periods longer than 24 hours. As an added bonus, the script will run completely in the background and __should NOT interfere with your daily routine.__

### Windows
1. Open *Task Scheduler* and click *Create Task*.
2. Choose *Run whether user is logged on or not* under *Security options* and check the box at the bottom that says *Hidden*.
3. Add a new trigger, either *On workstation unlock* for your specific username or *On a schedule* daily depending on what you want. 
4. When adding the action, point the program to *__python.exe__* (most likely located in *__C:/Program Files__*) and add the argument line `BingRewards/BingRewards.py -r`. In the *Start in* box, place the absolute path to where you've cloned this repository.
5. It's also recommended to select the option to only execute when there is a network connection available under the *Conditions* tab.

### Mac
1. Open *Automator* and choose *Application*
2. Search for *Run Shell Script* under *Utilities*
3. Erase any content and enter `python /absolute/path/to/BingRewards/BingRewards.py -r` with the correct path. If you have multiple versions of Python installed, you may need to include that absolute path as well. By default, Automator will use *__/usr/bin/python__*. You can determine yours by running `which python` in any terminal. 
4. Now do *File > Export..* and *Export As* *__run_mac.app__*. 

##### At Login
1. Navigate to *System Preferences > Users & Groups > Login Items* and add *__run_mac.app__*. Note, this will only get triggered after logging into your machine and not every time you unlock your computer.

##### At a Specific Time
1. For scheduling something daily, you can create a time-based job with cron. Open up the terminal and type: `crontab -e`. 
2. Now append the following line with the correct path: `0 0 * * * osascript /absolute/path/to/run_mac.app`. The second 0 is the hour (0-23) in your local timezone. Also note the default text editor for crontab is VIM so you'll need to hit `i` before inserting and finally `:wq` to write the changes and quit.

## Under the Hood
- Python 3.6
- ChromeDriver 2.35
- Selenium

## Disclaimer
- Results may vary if you are running a Mac. Most to all of the development was done on Windows.
- Storing passwords locally, even if they are hashed, should be handled with caution. **The user should avoid getting set up on a shared computer.** 
- Automation is a hobby and this project was a way to enhance my programming skills. As a result, it may also be seldomly maintained. 

## Known Issues
- Engagement in daily offers suddenly hangs.
- Quiz offers failing to complete.

These issues have been seen to be resolved running ChromeDriver outside of headless mode, however, at the time I have not provided a simple way to do this. Headless mode is a relatively new feature that allows Google Chrome to be launched in the background. Turning this feature off would interfere with the users daily routine. 

Some of these bug fixes may also be roled out in newer builds. You can ensure you have the latest release by deleting the contents of *__BingRewards/drivers/__* and the most up-to-date driver will automatically be downloaded the next time you run the program. 

## Future Work
- ~~Utilize Microsoft Edge's web driver to earn additional points.~~ (Solved with user agents!)

