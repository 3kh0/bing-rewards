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

