"""
Previous run completion status is saved in a log file run.json.
log.py's primary responsibility is reading in this log file
and converting it into a completion object within get_completion()

The completion object is passed into rewards.py
to ascertain what remaining tasks to run.

rewards.py returns an updated completion object which is
finally converted back into a new log entry
and then written to the log file within write()
"""
import os
from datetime import datetime
from dateutil import tz
import json


def get_current_datetime(tzinfo=tz.tzlocal()):
    return datetime.now().replace(tzinfo=tzinfo)


class HistLog:
    """
    The 'controller' for the
    search history, run history, and completion objects
    """

    __DATETIME_FORMAT = "%a, %b %d %Y %I:%M:%S%p"
    __OLD_DATETIME_FORMAT = "%a, %b %d %Y %I:%M%p"

    __LOCAL_TIMEZONE = tz.tzlocal()
    __PST_TIMEZONE = tz.gettz(
        "US/Alaska"
    )  # Alaska timezone, guards against Pacific Daylight Savings Time

    __RESET_HOUR = 0  # AM PST
    __MAX_HIST_LEN = 30  # days

    __COMPLETED_TRUE = "Successful"
    __COMPLETED_FALSE = "Failed {}"

    __EDGE_SEARCH_OPTION = "Edge Search"
    __WEB_SEARCH_OPTION = "Web Search"
    __MOBILE_SEARCH_OPTION = "Mobile Search"
    __OFFERS_OPTION = "Offers"
    __PUNCHCARD_OPTION = "Latest Punch Card Activity"
    __FITNESS_VIDEOS_OPTION = "Fitness Videos"

    def __init__(self, email, run_path, search_path, fitness_videos_path):
        self.email = email

        self.__run_log = RunHistoryJsonLog(run_path, email)
        self.__search_log = SearchHistoryJsonLog(search_path, email)
        self.__fitness_videos_log = FitnessVideosHistoryJsonLog(
            fitness_videos_path, email
        )
        self.__completion = Completion()

    def get_timestamp(self):
        return get_current_datetime().strftime(self.__DATETIME_FORMAT)

    def is_already_ran_today(self):
        try:
            last_ran = self.__run_log.user_entries[-1].split(": ")[0]
            try:
                last_ran = datetime.strptime(last_ran, self.__DATETIME_FORMAT)
            except ValueError:  # port old datetime_format
                last_ran = datetime.strptime(last_ran, self.__OLD_DATETIME_FORMAT)

            last_ran_pst = last_ran.replace(tzinfo=self.__LOCAL_TIMEZONE).astimezone(
                self.__PST_TIMEZONE
            )
            run_datetime_pst = get_current_datetime(self.__PST_TIMEZONE)
            delta_days = (run_datetime_pst.date() - last_ran_pst.date()).days
            is_already_ran_today = (
                delta_days == 0 and last_ran_pst.hour >= self.__RESET_HOUR
            ) or (delta_days == 1 and run_datetime_pst.hour < self.__RESET_HOUR)
        except IndexError:
            is_already_ran_today = False
        return is_already_ran_today

    def get_completion(self):
        # check if already ran today
        if self.is_already_ran_today():
            print(f'\n{self.__run_log.user_entries[-1].split(": ")}')
            completed = self.__run_log.user_entries[-1].split(": ")[1]
            if completed == self.__COMPLETED_TRUE:
                self.__completion.edge_search = True
                self.__completion.web_search = True
                self.__completion.mobile_search = True
                self.__completion.offers = True
                self.__completion.punchcard = True
                self.__completion.fitness_videos = True
            else:
                if self.__EDGE_SEARCH_OPTION not in completed:
                    self.__completion.edge_search = True
                if self.__WEB_SEARCH_OPTION not in completed:
                    self.__completion.web_search = True
                if self.__MOBILE_SEARCH_OPTION not in completed:
                    self.__completion.mobile_search = True
                if self.__OFFERS_OPTION not in completed:
                    self.__completion.offers = True
                if self.__PUNCHCARD_OPTION not in completed:
                    self.__completion.punchcard = True
                if self.__FITNESS_VIDEOS_OPTION not in completed:
                    self.__completion.fitness_videos = True
        else:
            # clear search history if account's first run of the day
            self.__search_log.user_entries = []

        return self.__completion

    def get_run_hist(self):
        return self.__run_log.user_entries

    def get_search_hist(self):
        return self.__search_log.user_entries

    def get_fitness_videos_hist(self):
        return self.__fitness_videos_log.user_entries

    def write(self, completion):
        self.__completion.update(completion)
        # create run.log entry based on updated Completion obj
        if not self.__completion.is_all_completed():
            failed = []
            if not self.__completion.is_edge_search_completed():
                failed.append(self.__EDGE_SEARCH_OPTION)
            if not self.__completion.is_web_search_completed():
                failed.append(self.__WEB_SEARCH_OPTION)
            if not self.__completion.is_mobile_search_completed():
                failed.append(self.__MOBILE_SEARCH_OPTION)
            if not self.__completion.is_offers_completed():
                failed.append(self.__OFFERS_OPTION)
            if not self.__completion.is_punchcard_completed():
                failed.append(self.__PUNCHCARD_OPTION)
            if not self.__completion.is_fitness_videos_completed():
                failed.append(self.__FITNESS_VIDEOS_OPTION)
            failed = ", ".join(failed)
            completion_msg = self.__COMPLETED_FALSE.format(failed)
        else:
            completion_msg = self.__COMPLETED_TRUE

        # write run log if first time running today OR
        # last log entry not success
        if (
            not self.is_already_ran_today()
            or self.__COMPLETED_TRUE not in self.__run_log.user_entries[-1]
        ):
            self.__run_log.add_entry_and_write(completion_msg, self.email)

        # write to search log, `search_log.user_entries` adds searches
        # when passed into Rewards()
        if self.__search_log.user_entries:
            self.__search_log.reattach_to_json(self.email)
            self.__search_log.write()

        # write to fitness video history log
        if self.__fitness_videos_log.user_entries:
            self.__fitness_videos_log.reattach_to_json(self.email)
            self.__fitness_videos_log.write()


class Completion:
    def __init__(self):
        self.edge_search = False
        self.web_search = False
        self.mobile_search = False
        self.offers = False
        self.punchcard = False
        self.fitness_videos = False

    def is_edge_search_completed(self):
        return self.edge_search

    def is_web_search_completed(self):
        return self.web_search

    def is_edge_and_web_search_completed(self):
        return self.web_search and self.edge_search

    def is_edge_and_mobile_search_completed(self):
        return self.mobile_search and self.edge_search

    def is_mobile_search_completed(self):
        return self.mobile_search

    def is_both_searches_completed(self):
        return self.is_edge_and_web_search_completed() and self.mobile_search

    def is_offers_completed(self):
        return self.offers

    def is_punchcard_completed(self):
        return self.punchcard

    def is_fitness_videos_completed(self):
        return self.fitness_videos

    def is_web_device_completed(self):
        """These searches require web driver"""
        return self.web_search and self.offers and self.punchcard

    def is_all_completed(self):
        return (
            self.is_edge_and_web_search_completed()
            and self.mobile_search
            and self.offers
            and self.punchcard
            and self.fitness_videos
        )

    def update(self, completion):
        """
        Updates the run.log based on the
        - state after the most recent run
        - state prior to most recent run, IF already ran today
        The first is obvious, the 2nd not as much.

        If a search/action was previously successful today
        , i.e is not marked failed in run.log,
        and when re-run, is considered failed,
        it remains un-failed
        due to max()

        This is useful when user presses ctrl + c, but also
        when user re-runs a punchcard after a prev success
        """
        self.edge_search = max(self.edge_search, completion.edge_search)
        self.web_search = max(self.web_search, completion.web_search)
        self.mobile_search = max(self.mobile_search, completion.mobile_search)
        self.offers = max(self.offers, completion.offers)
        self.punchcard = max(self.punchcard, completion.punchcard)
        self.fitness_videos = max(self.fitness_videos, completion.fitness_videos)

    def is_search_type_completed(self, search_type):
        if search_type == "web":
            return self.is_edge_and_web_search_completed()
        elif search_type == "mobile":
            return self.is_edge_and_mobile_search_completed()
        elif search_type == "both":
            return self.is_both_searches_completed()
        elif search_type == "offers":
            return self.is_offers_completed()
        elif search_type == "punch card":
            return self.is_punchcard_completed()
        elif search_type == "fitness videos":
            return self.is_fitness_videos_completed()
        elif search_type in ("all", "remaining"):
            return self.is_all_completed()


class BaseJsonLog:
    """
    Base class to read and write .json logs.
    For each json log file, the keys are the username/emails
    and the values are the log entries for that user

    The flow for each log is to
    1. read in the json for all the users
    2. Obtain the log entries as a list for
    just the current user, i.e self.user_entries
    3. Expose just self.user_entries to HistLog, append any new entries
    4. Re-attach the updated user_entries back to the original json object
    5. Write (overwrite!) the json back to the log file
    """

    __DATETIME_FORMAT = "%a, %b %d %Y %I:%M:%S%p"
    LOCAL_TIMEZONE = tz.tzlocal()

    def __init__(self, log_path, email):
        self.log_path = log_path
        self.read()
        self.user_entries = self.data.get(email, [])

    def read(self):
        if not os.path.exists(self.log_path):
            self.data = {}
        else:
            with open(
                self.log_path,
            ) as f:
                self.data = json.load(f)

    def add_user_entry(self, entry, include_log_dt):
        if include_log_dt:
            log_time = get_current_datetime().strftime(self.__DATETIME_FORMAT)
            entry = f"{log_time}: {entry}"
        self.user_entries.append(entry)
        self.user_entries = self.user_entries[-self.MAX_SIZE :]

    def reattach_to_json(self, email):
        """attach user log entries to json dict"""
        self.data[email] = self.user_entries

    def write(self):
        with open(self.log_path, "w") as f:
            json.dump(self.data, f, indent=4, sort_keys=True)

    def add_entry_and_write(self, entry, email, include_log_dt=True):
        self.add_user_entry(entry, include_log_dt)
        self.reattach_to_json(email)
        self.write()


class StatsJsonLog(BaseJsonLog):
    MAX_SIZE = 300

    def __init__(self, log_path, email):
        super().__init__(log_path, email)


class RunHistoryJsonLog(BaseJsonLog):
    MAX_SIZE = 365

    def __init__(self, log_path, email):
        super().__init__(log_path, email)


class SearchHistoryJsonLog(BaseJsonLog):
    MAX_SIZE = 1

    def __init__(self, log_path, email):
        super().__init__(log_path, email)


class FitnessVideosHistoryJsonLog(BaseJsonLog):
    MAX_SIZE = 100

    def __init__(self, log_path, email):
        super().__init__(log_path, email)
