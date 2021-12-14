import sys
import os
from src.rewards import Rewards
from src.log import HistLog
import logging
import base64
from options import parse_arguments

DRIVERS_DIR = "drivers"
DRIVER = "chromedriver"

LOG_DIR = "logs"
ERROR_LOG = "error.log"
RUN_LOG = "run.log"
SEARCH_LOG = "search.log"

DEBUG = True


def __decode(encoded):
    return base64.b64decode(encoded).decode()


def complete_search(rewards, completion, search_type, search_hist):
    print(f"\n\tYou selected {search_type}\n")
    if not completion.is_search_type_completed(search_type):
        rewards.complete_search_type(search_type, completion, search_hist)
    else:
        print(f'{search_type.capitalize()} already completed')


def __main():
    args = parse_arguments()
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

    #browser cookies
    cookies = args.cookies

    # get credentials
    if args.email and args.password:
        email = args.email
        password = args.password
        telegrambotkey = args.telegrambotkey
        telegramuserid = args.telegramuserid
        cookies = False
    else:
        try:
            from src import config
        except ImportError:
            print("\nFailed to import configuration file")
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(message)s',
                filename=os.path.join(LOG_DIR, ERROR_LOG)
            )
            logging.exception(hist_log.get_timestamp())
            logging.debug("")
            raise
        email = __decode(config.credentials['email'])
        password = __decode(config.credentials['password'])
        telegrambotkey = config.credentials['telegrambotkey']
        telegramuserid = config.credentials['telegramuserid']

    if not os.path.exists(DRIVERS_DIR):
        os.mkdir(DRIVERS_DIR)

    rewards = Rewards(
        os.path.join(DRIVERS_DIR, DRIVER), email, password,telegrambotkey,telegramuserid, DEBUG, args.headless, cookies
    )
    completion = hist_log.get_completion()
    search_hist = hist_log.get_search_hist()
    search_type = args.search_type

    try:
        complete_search(rewards, completion, search_type, search_hist)
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
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(message)s',
            filename=os.path.join(LOG_DIR, ERROR_LOG)
        )
        logging.exception(hist_log.get_timestamp())
        logging.debug("")
        hist_log.write(rewards.completion, rewards.search_hist)
        raise


if __name__ == "__main__":
    __main()
