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

    # get credentials
    if args.email and args.password:
        email = args.email
        password = args.password
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

    if not os.path.exists(DRIVERS_DIR):
        os.mkdir(DRIVERS_DIR)
    rewards = Rewards(
        os.path.join(DRIVERS_DIR, DRIVER), email, password, DEBUG, args.headless
    )
    completion = hist_log.get_completion()

    try:
        if args.search_type == 'remaining':
            print("\n\t{}\n".format("You selected remaining"))

            if not completion.is_all_completed():
                #complete_all() is fastest method b/c it doesn't open new webdriver for each new search type, so even if already completed method is tried again, it has very low overhead.
                if not completion.is_web_search_completed(
                ) and not completion.is_mobile_search_completed():
                    rewards.complete_all(hist_log.get_search_hist())
                #higher overhead, opens a new webdriver for each unfinished search type
                else:
                    if not completion.is_edge_search_completed():
                        rewards.complete_edge_search(hist_log.get_search_hist())
                    if not completion.is_web_search_completed():
                        rewards.complete_web_search(hist_log.get_search_hist())
                    if not completion.is_offers_completed():
                        rewards.complete_offers()
                    if not completion.is_mobile_search_completed():
                        rewards.complete_mobile_search(
                            hist_log.get_search_hist()
                        )

                hist_log.write(rewards.completion, rewards.search_hist)
                completion = hist_log.get_completion()
                if not completion.is_all_completed(
                ):  # check again, log if any failed
                    logging.basicConfig(
                        level=logging.DEBUG,
                        format='%(message)s',
                        filename=os.path.join(LOG_DIR, ERROR_LOG)
                    )
                    logging.debug(hist_log.get_timestamp())
                    for line in rewards.stdout:
                        logging.debug(line)
                    logging.debug("")

            else:
                print("Nothing remaining")
        elif args.search_type == 'web':
            print("\n\t{}\n".format("You selected web search"))
            if not completion.is_edge_and_web_search_completed():
                if not completion.is_edge_search_completed():
                    rewards.complete_edge_search(hist_log.get_search_hist())
                if not completion.is_web_search_completed():
                    rewards.complete_web_search(hist_log.get_search_hist())
                hist_log.write(rewards.completion, rewards.search_hist)
            else:
                print('Web search already completed')
        elif args.search_type == 'mobile':
            print("\n\t{}\n".format("You selected mobile search"))
            if not completion.is_edge_and_mobile_search_completed():
                if not completion.is_edge_search_completed():
                    rewards.complete_edge_search(hist_log.get_search_hist())
                if not completion.is_mobile_search_completed():
                    rewards.complete_mobile_search(hist_log.get_search_hist())
                hist_log.write(rewards.completion, rewards.search_hist)
            else:
                print('Mobile search already completed')
        elif args.search_type == 'both':
            print(
                "\n\t{}\n".format("You selected both searches (web & mobile)")
            )
            if not completion.is_both_searches_completed():
                rewards.complete_both_searches(hist_log.get_search_hist())
                hist_log.write(rewards.completion, rewards.search_hist)
            else:
                print('Both searches already completed')
        elif args.search_type == 'offers':
            print("\n\t{}\n".format("You selected offers"))
            if not completion.is_offers_completed():
                rewards.complete_offers()
                hist_log.write(rewards.completion, rewards.search_hist)
            else:
                print('Offers already completed')
        elif args.search_type == 'all':
            print("\n\t{}\n".format("You selected all"))
            if not completion.is_all_completed():
                rewards.complete_all(hist_log.get_search_hist())
                hist_log.write(rewards.completion, rewards.search_hist)
            else:
                print('All already completed')

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
