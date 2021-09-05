import sys
import os
from src.rewards import Rewards
from src.log import HistLog
import logging

DRIVERS_DIR = "drivers"
DRIVER = "chromedriver"

LOG_DIR = "logs"
ERROR_LOG = "error.log"
RUN_LOG = "run.log"
SEARCH_LOG = "search.log"

DEBUG = True
HEADLESS = True


def __main(arg0, arg1):
    # change to top dir
    dir_run_from = os.getcwd()
    top_dir = os.path.dirname(arg0)
    if top_dir and top_dir != dir_run_from:
        os.chdir(top_dir)

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    hist_log = HistLog(
        os.path.join(LOG_DIR, RUN_LOG), os.path.join(LOG_DIR, SEARCH_LOG)
    )

    # get credentials
    try:
        from src import config
    except:
        print("\nFailed to import configuration file")
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(message)s',
            filename=os.path.join(LOG_DIR, ERROR_LOG)
        )
        logging.exception(hist_log.get_timestamp())
        logging.debug("")
        raise

    if not os.path.exists(DRIVERS_DIR):
        os.mkdir(DRIVERS_DIR)
    rewards = Rewards(
        os.path.join(DRIVERS_DIR, DRIVER), config.credentials["email"],
        config.credentials["password"], DEBUG, HEADLESS
    )
    completion = hist_log.get_completion()

    try:
        if arg1 in ["w", "web"]:
            print("\n\t{}\n".format("You selected web search"))
            if not completion.is_edge_and_web_search_completed():
                if not completion.is_edge_search_completed():
                    rewards.complete_edge_search(hist_log.get_search_hist())
                if not completion.is_web_search_completed():
                    rewards.complete_web_search(hist_log.get_search_hist())
                hist_log.write(rewards.completion, rewards.search_hist)
            else:
                print('Web search already completed')
        elif arg1 in ["m", "mobile"]:
            print("\n\t{}\n".format("You selected mobile search"))
            if not completion.is_edge_and_mobile_search_completed():
                if not completion.is_edge_search_completed():
                    rewards.complete_edge_search(hist_log.get_search_hist())
                if not completion.is_mobile_search_completed():
                    rewards.complete_mobile_search(hist_log.get_search_hist())
                hist_log.write(rewards.completion, rewards.search_hist)
            else:
                print('Mobile search already completed')
        elif arg1 in ["b", "both"]:
            print(
                "\n\t{}\n".format("You selected both searches (web & mobile)")
            )
            if not completion.is_both_searches_completed():
                rewards.complete_both_searches(hist_log.get_search_hist())
                hist_log.write(rewards.completion, rewards.search_hist)
            else:
                print('Both searches already completed')
        elif arg1 in ["o", "other"]:
            print("\n\t{}\n".format("You selected offers"))
            if not completion.is_offers_completed():
                rewards.complete_offers()
                hist_log.write(rewards.completion, rewards.search_hist)
            else:
                print('Offers already completed')
        elif arg1 in ["a", "all"]:
            print("\n\t{}\n".format("You selected all"))
            if not completion.is_all_completed():
                rewards.complete_all(hist_log.get_search_hist())
                hist_log.write(rewards.completion, rewards.search_hist)
            else:
                print('All already completed')
        else:
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
    except:
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
    args = sys.argv

    if len(args) == 1:
        out = "Enter \t{}, \n\t{}, \n\t{}, \n\t{}, \n\t{}, \n\t{} \nInput: \t"
        input_message = out.format(
            "w for web", "m for mobile", "b for both", "o for offers",
            "a for all", "r for remaining (default)"
        )

        try:
            arg1 = raw_input(input_message)  # python 2
        except:
            arg1 = input(input_message)  # python 3
        arg1 = arg1.lower()

        __main(args[0], arg1)

    elif len(args) == 2:
        arg1 = args[1].lower()
        assert arg1 in [
            "-w", "--web", "-m", "--mobile", "-b", "--both", "-o", "--offers",
            "-a", "-all", "-r", "--remaining"
        ]

        __main(args[0], arg1.replace("-", ""))

    else:
        print("Incorrect number of arguments")
