import sys
import os
import logging
import base64
import json
from options import parse_search_args
from src.rewards import Rewards
from src.log import HistLog, StatsJsonLog
from src.messengers import TelegramMessenger, DiscordMessenger, BaseMessenger
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
        raise ImportError(
            "'config.json' file does not exist. Please run `python setup.py`.\nIf you are a previous user, existing credentials will be automatically ported over.")
    return config


def get_telegram_messenger(config, args):
    telegram_api_token = __decode(config.get('telegram_api_token'))
    telegram_userid = __decode(config.get('telegram_userid'))
    telegram_messenger = None

    if not args.telegram or not telegram_api_token or not telegram_userid:
        if args.telegram:
            print('You have selected Telegram, but config file is missing `api token` or `userid`. Please re-run setup.py with additional arguments if you want Telegram notifications.')
    else:
        telegram_messenger = TelegramMessenger(
            telegram_api_token, telegram_userid)
    return telegram_messenger


def get_discord_messenger(config, args):
    discord_webhook_url = __decode(config.get('discord_webhook_url'))
    discord_messenger = None

    if not args.discord or not discord_webhook_url:
        if args.discord:
            print('You have selected Discord, but the config file is missing a webhook_url. Please re-run setup.py with additional arguments if you want Discord notifications.')
    else:
        discord_messenger = DiscordMessenger(discord_webhook_url)
    return discord_messenger


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
    discord_messenger = get_discord_messenger(config, args)
    messengers: list[BaseMessenger] = [messenger for messenger in [
        telegram_messenger, discord_messenger] if messenger is not None]
    google_sheets_reporting = get_google_sheets_reporting(config, args)
    rewards = Rewards(email, password, DEBUG, args.headless, args.cookies,
                      args.driver, args.nosandbox, args.google_trends_geo, messengers)

    try:
        complete_search(rewards, completion, args.search_type, search_hist)
        hist_log.write(rewards.completion)
        completion = hist_log.get_completion()

        if hasattr(rewards, 'stats'):
            formatted_stat_str = "; ".join(rewards.stats.stats_str)
            stats_log.add_entry_and_write(formatted_stat_str, email)

            run_hist_str = hist_log.get_run_hist()[-1].split(': ')[1]

            for messenger in messengers:
                messenger.send_reward_message(
                    rewards.stats.stats_str, run_hist_str, email)

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

        if len(messengers):
            # send error msg to telegram
            import traceback
            error_msg = traceback.format_exc()

        for messenger in messengers:
            messenger.send_message(error_msg)
        raise


if __name__ == "__main__":
    main()
