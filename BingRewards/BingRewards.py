import sys
import os
import logging
import json
from options import parse_search_args
from setup import CONFIG_FILE_PATH, process_microsoft_account_args
from src.rewards import Rewards
from src.log import HistLog, StatsJsonLog
from src.messengers import TelegramMessenger, DiscordMessenger, BaseMessenger
from src.google_sheets_reporting import GoogleSheetsReporting
from selenium.common.exceptions import WebDriverException

LOG_DIR = "logs"
ERROR_LOG = "error.log"
RUN_LOG = "run.json"
SEARCH_LOG = "search.json"
STATS_LOG = "stats.json"
FITNESS_VIDEOS_LOG = "fitness_videos.json"
# CONFIG_FILE_PATH = "config/config.json"
DEBUG = True


def _log_hist_log(hist_log):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        filename=os.path.join(LOG_DIR, ERROR_LOG),
    )
    logging.exception(hist_log.get_timestamp())
    logging.debug("")


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
            f"'{CONFIG_FILE_PATH}' file does not exist. Please "
            "run `python setup.py`.\n"
            "If you are a previous user, existing credentials "
            "will be automatically ported over."
        )
    return config


def get_telegram_messenger(config, args):
    telegram_api_token = config.get("telegram_api_token")
    telegram_userid = config.get("telegram_userid")
    telegram_messenger = None

    if not args.telegram or not telegram_api_token or not telegram_userid:
        if args.telegram:
            print(
                "You have selected Telegram, but config file "
                "is missing `api token` or `userid`. "
                "Please re-run setup.py with additional arguments "
                "if you want Telegram notifications."
            )
    else:
        telegram_messenger = TelegramMessenger(telegram_api_token, telegram_userid)
    return telegram_messenger


def get_discord_messenger(config, args):
    discord_webhook_url = config.get("discord_webhook_url")
    discord_messenger = None

    if not args.discord or not discord_webhook_url:
        if args.discord:
            print(
                "You have selected Discord, but the config "
                "file is missing a webhook_url. "
                "Please re-run setup.py with additional arguments "
                "if you want Discord notifications."
            )
    else:
        discord_messenger = DiscordMessenger(discord_webhook_url)
    return discord_messenger


def get_google_sheets_reporting(config, args):
    sheet_id = config.get("google_sheets_sheet_id")
    tab_name = config.get("google_sheets_tab_name")

    if args.google_sheets and sheet_id and tab_name:
        google_sheets_reporting = GoogleSheetsReporting(sheet_id, tab_name)
    else:
        if args.google_sheets:
            print(
                "You have selected Google Sheets reporting, but main config"
                " file is missing sheet_id or tab_name. Please re-run setup.py"
                " with additional arguments if you want Google Sheets"
                " reporting."
            )
        google_sheets_reporting = None
    return google_sheets_reporting


def message_stats(messengers, google_sheets_reporting, rewards, hist_log, email):
    """Send run notification using app"""

    run_hist_str = hist_log.get_run_hist()[-1].split(": ")[1]
    for messenger in messengers:
        messenger.send_reward_message(rewards.stats.stats_str, run_hist_str, email)

    if google_sheets_reporting:
        google_sheets_reporting.add_row(rewards.stats, email)


def handle_search_exception(hist_log, rewards, messengers):
    """
    For each exception, always do the following:
    1. write to error.log
    2. Write to run.log current completion status
    3. send an alert if user has a messenger
    """

    _log_hist_log(hist_log)
    hist_log.write(rewards.completion)

    # send error msg to telegram
    import traceback

    error_msg = traceback.format_exc()

    for messenger in messengers:
        messenger.send_message(error_msg)
    return error_msg


def run_account(email, password, args, messengers, google_sheets_reporting):
    """Run one individual account n times"""
    rewards = Rewards(
        email,
        password,
        DEBUG,
        args.headless,
        args.cookies,
        args.driver,
        args.nosandbox,
        args.google_trends_geo,
        messengers,
    )

    stats_log = StatsJsonLog(os.path.join(LOG_DIR, STATS_LOG), email)

    hist_log = HistLog(
        email,
        os.path.join(LOG_DIR, RUN_LOG),
        os.path.join(LOG_DIR, SEARCH_LOG),
        os.path.join(LOG_DIR, FITNESS_VIDEOS_LOG),
    )

    print(
        f"""\n\nRunning with:
        Account: {email}
        Search type: {args.search_type.capitalize()}"""
    )
    completion = hist_log.get_completion()
    if completion.is_search_type_completed(args.search_type):
        print(f"{args.search_type.capitalize()} already completed\n")
        return

    excluded_searches = list(args.exclude) if args.exclude else []
    current_attempts = 0

    # Run search 'n' times per account
    while (
        not completion.is_search_type_completed(args.search_type)
        and current_attempts < args.max_attempts_per_account
    ):
        search_hist = hist_log.get_search_hist()
        fitness_videos_hist = hist_log.get_fitness_videos_hist()

        print(f"\n\nRun {current_attempts+1} [{email}]:")

        try:
            rewards.complete_search_type(
                args.search_type,
                excluded_searches,
                completion,
                search_hist,
                fitness_videos_hist,
            )
            hist_log.write(rewards.completion)

        except (Exception, KeyboardInterrupt) as e:  # catch *all* exceptions
            error_msg = handle_search_exception(hist_log, rewards, messengers)

            if isinstance(e, KeyboardInterrupt):
                raise
            # some selenium exception, try again
            elif isinstance(e, WebDriverException):
                print(
                    f"\n\nWebDriverException, will try again for {email} if "
                    f"runs remain:\n{error_msg}"
                )
            # unknown non-selenium exception, next account
            else:
                print(
                    f"\n\nABORTING run(s) for {email} due to uncaught"
                    f"exception:\n{error_msg}"
                )
                return

        current_attempts += 1
        completion = hist_log.get_completion()

        # Send notifcations after each run
        if hasattr(rewards, "stats"):
            formatted_stat_str = "; ".join(rewards.stats.stats_str)
            stats_log.add_entry_and_write(formatted_stat_str, email)

            message_stats(messengers, google_sheets_reporting, rewards, hist_log, email)

    # log if searches still failing after running 'n' times
    if not completion.is_search_type_completed(args.search_type):
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(message)s",
            filename=os.path.join(LOG_DIR, ERROR_LOG),
        )
        logging.debug(hist_log.get_timestamp())
        for line in rewards.stdout:
            logging.debug(line)
        logging.debug("")


def main():
    """
    Run all accounts
    """
    # change to top dir
    dir_run_from = os.getcwd()
    top_dir = os.path.dirname(sys.argv[0])
    if top_dir and top_dir != dir_run_from:
        os.chdir(top_dir)

    config = get_config()

    args = parse_search_args()
    if args.email and args.password:
        microsoft_accounts = process_microsoft_account_args(args)
    else:
        microsoft_accounts = config["microsoft_accounts"]

    # Always turn off cookies if running multiple accounts
    if len(microsoft_accounts) > 1 and args.cookies:
        args.cookies = False
        print("\nCookies turned off due to running multiple accounts.\n")

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # telegram credentials
    telegram_messenger = get_telegram_messenger(config, args)
    discord_messenger = get_discord_messenger(config, args)
    messengers: list[BaseMessenger] = [
        messenger
        for messenger in [telegram_messenger, discord_messenger]
        if messenger is not None
    ]
    google_sheets_reporting = get_google_sheets_reporting(config, args)

    for microsoft_account in microsoft_accounts:
        run_account(
            microsoft_account["email"],
            microsoft_account["password"],
            args,
            messengers,
            google_sheets_reporting,
        )


if __name__ == "__main__":
    main()
