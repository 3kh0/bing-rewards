import sys
import os
from src.rewards import Rewards
from src.log import HistLog, StatsJsonLog
from src.telegram import TelegramMessenger
import logging
import base64
from options import parse_arguments


LOG_DIR = "logs"
ERROR_LOG = "error.log"
RUN_LOG = "run.log"
SEARCH_LOG = "search.log"
STATS_LOG = "stats.json"

DEBUG = True


def __decode(encoded):
    if encoded:
        return base64.b64decode(encoded).decode()


def get_telegram_messenger(config, args):
    telegram_api_token = __decode(config.credentials.get('telegram_api_token'))
    telegram_userid = __decode(config.credentials.get('telegram_userid'))
    if not args.telegram or not telegram_api_token or not telegram_userid:
        telegram_messenger = None
    else:
        telegram_messenger = TelegramMessenger(telegram_api_token, telegram_userid)
    return telegram_messenger


def complete_search(rewards, completion, search_type, search_hist):
    print(f"\nYou selected {search_type}")
    if not completion.is_search_type_completed(search_type):
        rewards.complete_search_type(search_type, completion, search_hist)
    else:
        print(f'{search_type.capitalize()} already completed\n')


def __main():
    # change to top dir
    dir_run_from = os.getcwd()
    top_dir = os.path.dirname(sys.argv[0])
    if top_dir and top_dir != dir_run_from:
        os.chdir(top_dir)

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    hist_log = HistLog(
        os.path.join(LOG_DIR, RUN_LOG), os.path.join(LOG_DIR, SEARCH_LOG)
    )
    stats_log = StatsJsonLog(os.path.join(LOG_DIR, STATS_LOG))

    try:
        from src import config
    except ImportError:
        print("\nFailed to import configuration file")
        _log_hist_log(hist_log)
        raise

    args = parse_arguments()
    # browser cookies
    cookies = args.cookies

    # microsoft email/pw
    if args.email and args.password:
        email = args.email
        password = args.password
        cookies = False
    else:
        email = __decode(config.credentials['email'])
        password = __decode(config.credentials['password'])

    # telegram credentials
    telegram_messenger = get_telegram_messenger(config, args)

    rewards = Rewards(email, password, DEBUG, args.headless, cookies, args.driver)
    completion = hist_log.get_completion()
    search_hist = hist_log.get_search_hist()
    search_type = args.search_type

    try:
        complete_search(rewards, completion, search_type, search_hist)

        if hasattr(rewards, 'stats'):
            stats_log.write(rewards.stats, email)
            if telegram_messenger:
                telegram_messenger.send_reward_message(rewards.stats, email)

        hist_log.write(rewards.completion, rewards.search_hist)
        completion = hist_log.get_completion()

        # check again, log if any failed
        if not completion.is_search_type_completed(search_type):
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
        hist_log.write(rewards.completion, rewards.search_hist)
        if telegram_messenger:
            # send error msg to telegram
            import traceback
            error_msg = traceback.format_exc()
            telegram_messenger.send_message(error_msg)
        raise


def _log_hist_log(hist_log):
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(message)s',
        filename=os.path.join(LOG_DIR, ERROR_LOG)
    )
    logging.exception(hist_log.get_timestamp())
    logging.debug("")


if __name__ == "__main__":
    __main()
