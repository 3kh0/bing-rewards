import sys
import os
import logging
import base64
import json
import requests
from options import parse_search_args
from src.rewards import Rewards
from src.log import HistLog, StatsJsonLog
from src.telegram import TelegramMessenger
from src.google_sheets_reporting import GoogleSheetsReporting

LOG_DIR = "logs"
ERROR_LOG = "error.log"
RUN_LOG = "run.json"
SEARCH_LOG = "search.json"
STATS_LOG = "stats.json"
CONFIG_FILE_PATH = "config/config.json"
DEBUG = True


def _log_hist_log(hist_log):
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(message)s',
        filename=os.path.join(LOG_DIR, ERROR_LOG)
    )
    logging.exception(hist_log.get_timestamp())
    logging.debug("")


def __decode(encoded):
    if encoded:
        return base64.b64decode(encoded).decode()


def get_config():
    if os.path.isfile(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH) as f:
                config = json.load(f)
        except ValueError:
            print("There was an error decoding the 'config.json' file")
            raise
    else:
        raise ImportError("'config.json' file does not exist. Please run `python setup.py`.\nIf you are a previous user, existing credentials will be automatically ported over.")
    return config


def get_telegram_messenger(config, args):
    telegram_api_token = __decode(config.get('telegram_api_token'))
    telegram_userid = __decode(config.get('telegram_userid'))
    if not args.telegram or not telegram_api_token or not telegram_userid:
        if args.telegram:
            print('You have selected Telegram, but config file is missing `api token` or `userid`. Please re-run setup.py with additional arguments if you want Telegram notifications.')
        telegram_messenger = None
    else:
        telegram_messenger = TelegramMessenger(telegram_api_token, telegram_userid)
    return telegram_messenger

def get_discord(config, args):
    discord_webhook = __decode(config.get('discord_webhook'))
    if args.discord_webhook:
        if not discord_webhook:
            print('You have selected Discord, but the config file is missing a webhook. Please re-run setup.py with additional arguments if you want Discord notifications.')
            discord_webhook = None
    return discord_webhook

def get_google_sheets_reporting(config, args):
    sheet_id = __decode(config.get('google_sheets_sheet_id'))
    tab_name = __decode(config.get('google_sheets_tab_name'))

    if args.google_sheets and sheet_id and tab_name:
        google_sheets_reporting = GoogleSheetsReporting(sheet_id, tab_name)
    else:
        if args.google_sheets:
            print('You have selected Google Sheets reporting, but main config file is missing sheet_id or tab_name. Please re-run setup.py with additional arguments if you want Google Sheets reporting.')
        google_sheets_reporting = None
    return google_sheets_reporting


def complete_search(rewards, completion, search_type, search_hist):
    print(f"\nYou selected {search_type}")
    if not completion.is_search_type_completed(search_type):
        rewards.complete_search_type(search_type, completion, search_hist)
    else:
        print(f'{search_type.capitalize()} already completed\n')


def main():
    # change to top dir
    dir_run_from = os.getcwd()
    top_dir = os.path.dirname(sys.argv[0])
    if top_dir and top_dir != dir_run_from:
        os.chdir(top_dir)

    config = get_config()

    args = parse_search_args()
    if args.email and args.password:
        email = args.email
        password = args.password
        args.cookies = False
    else:
        email = __decode(config['email'])
        password = __decode(config['password'])

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    stats_log = StatsJsonLog(os.path.join(LOG_DIR, STATS_LOG), email)
    hist_log = HistLog(email,
        os.path.join(LOG_DIR, RUN_LOG), os.path.join(LOG_DIR, SEARCH_LOG))

    completion = hist_log.get_completion()
    search_hist = hist_log.get_search_hist()

    # telegram credentials
    telegram_messenger = get_telegram_messenger(config, args)
    discord = get_discord(config, args)
    google_sheets_reporting = get_google_sheets_reporting(config, args)
    rewards = Rewards(email, password, DEBUG, args.headless, args.cookies, args.driver, args.nosandbox)

    try:
        complete_search(rewards, completion, args.search_type, search_hist)
        hist_log.write(rewards.completion)
        completion = hist_log.get_completion()

        if hasattr(rewards, 'stats'):
            formatted_stat_str = "; ".join(rewards.stats.stats_str)
            stats_log.add_entry_and_write(formatted_stat_str, email)

            if telegram_messenger:
                run_hist_str = hist_log.get_run_hist()[-1].split(': ')[1]
                telegram_messenger.send_reward_message(rewards.stats.stats_str, run_hist_str, email)
            
            if discord:
                discord_message = email + ":\n\n" + "\n".join(rewards.stats.stats_str)
                discord_content = {
                    "username" : "Bing Rewards Bot",
                    "content" : discord_message
                }
                requests.post(discord, json=discord_content)

            if google_sheets_reporting:
                google_sheets_reporting.add_row(rewards.stats, email)

        # check again, log if any failed
        if not completion.is_search_type_completed(args.search_type):
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(message)s',
                filename=os.path.join(LOG_DIR, ERROR_LOG)
            )
            logging.debug(hist_log.get_timestamp())
            for line in rewards.stdout:
                logging.debug(line)
            logging.debug("")

    except:  # catch *all* exceptions
        _log_hist_log(hist_log)
        hist_log.write(rewards.completion)
        if telegram_messenger:
            # send error msg to telegram
            import traceback
            error_msg = traceback.format_exc()
            telegram_messenger.send_message(error_msg)
        raise


if __name__ == "__main__":
    main()
