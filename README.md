An automated solution using Python and Selenium for earning daily Microsoft Rewards points in all categories including web, mobile, and offers.

- [Getting Started (Local set-up)](#getting-started--local-set-up-)
  * [Additional info](#additional-info)
  * [Command Line Arguments](#command-line-arguments)
    + [Examples](#examples)
- [Acknowledgment](#acknowledgment)

<small><i><a href='http://github.com/3kh0/readme-toc/'>Table of contents generated with readme-toc</a></i></small>

Only `USA` website is guaranteed to be supported.

In place of GitHub which disabled this project in Jan 2023, there is now a [Discord Server](https://discord.gg/w326CR9gNv) to receive Bing Rewards updates and discuss the tool with other users.

## Getting Started (Local set-up)
Note: If using Docker, go directly to `/docs/docker_setup` for further instructions

1. Download [Chrome](https://www.google.com/chrome/) or [Edge](https://www.microsoft.com/edge)
2. Install [Python3](https://www.python.org/downloads/)
3. Install the requirements.txt file included in the repo: `pip install -r BingRewards/requirements.txt`
4. Create/update the config file by running `python BingRewards/setup.py`. Multiple accounts is supported.
	 -  **Please note**: Your credentials will be stored in plain text
5. You must have signed onto your account using this machine before. 
	- Open Chrome or Edge and visit https://login.live.com. The site may ask to send you a verification email or text.
	- Then, go to https://rewards.bing.com/ and go through the intro pages.
6. Run `python BingRewards/BingRewards.py` to start earning points. 
	- You may need to add `-nsb` flag if running on Linux, including for Docker 
8. Occasionally, update to the latest code by running `./bing-rewards-master/update.sh`
9. Optional alerting: You can receive alerts for the following services, see `/docs` folder for additional info:
	- Telegram
	- Discord
	- Google Sheets

### Additional info
There is additional info in the [/docs folder](https://bitbucket.org/bing-rewards/bing-rewards/src/master/docs/) for the following:

- docker set-up
- telegram/discord/google sheets set-up
- automated scheduling
- login options (passwordless set-up)
- multiple accounts set-up

### Command Line Arguments
There are a growing number of command-line argument options. Here are a few to note:
- `-r` or `--remaining`: remaining tasks - this is the *default* option
- `-nhl` or `--no-headless`: Don't run in headless mode. This is a non-default option.
- `-nsb` or `--no-sandbox`: Run browser in [no-sandbox mode](https://unix.stackexchange.com/a/68951). Useful for *Linux*. This is a non-default option.

To see the remaining argument options, please run:
```sh
python BingRewards.py -h
```

#### Examples
The following `python BingRewards.py` 
actually translates to `python BingRewards.py -r -hl -d chrome`, i.e run the remaining searches in chrome headless mode.

Here's an example of running non-default arguments
`python BingRewards.py -w -nhl -e my_email@gmail.com -p`, i.e run web searches in non-headless mode with the specified email, the password will be prompted separately.

## Acknowledgment
- The original author took down the code from their GitHub back in July 2018. The author gave me permission to re-upload and maintain but wishes to stay anonymous. I will continue to maintain it until this page says otherwise.
- GitHub hosting and Discord server by `3kh0`
- UK quiz updates by `chris987789`
- 2FA code by `revolutionisme`
- Telegram notifications by `hoseininjast`
- Punch card, dashboard JSON, 'This or That' perfect score, and more based on `Charles Bel's` wonderful [repo](https://github.com/charlesbel/Microsoft-Rewards-Farmer).
- Microsoft Edge support by `Summon528`
