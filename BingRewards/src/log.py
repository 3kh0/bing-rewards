import os
from datetime import datetime
from dateutil import tz
import json


class HistLog:
    __DATETIME_FORMAT = "%a, %b %d %Y %I:%M%p"

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

    def __init__(self, run_path, search_path, run_datetime=datetime.now()):
        self.run_path = run_path
        self.search_path = search_path
        self.__run_datetime = run_datetime.replace(tzinfo=self.__LOCAL_TIMEZONE)
        self.__run_hist = self.__read(run_path)
        self.__search_hist = self.__read(search_path)
        self.__completion = Completion()

    def __read(self, path):
        if not os.path.exists(path):
            return []
        else:
            with open(path, "r") as log:
                return [line.strip("\n") for line in log.readlines()]

    def get_timestamp(self):
        return self.__run_datetime.strftime(self.__DATETIME_FORMAT)

    def get_completion(self):
        # check if already ran today
        if len(self.__run_hist) > 0:
            print(self.__run_hist[-1].split(": "))
            last_ran, completed = self.__run_hist[-1].split(": ")

            last_ran_pst = datetime.strptime(last_ran, self.__DATETIME_FORMAT).replace(tzinfo=self.__LOCAL_TIMEZONE).astimezone(self.__PST_TIMEZONE)
            run_datetime_pst = self.__run_datetime.astimezone(
                self.__PST_TIMEZONE
            )
            delta_days = (run_datetime_pst.date() - last_ran_pst.date()).days
            is_already_ran_today = (
                (delta_days == 0 and last_ran_pst.hour >= self.__RESET_HOUR) or
                (delta_days == 1 and run_datetime_pst.hour < self.__RESET_HOUR)
            )
            if is_already_ran_today:
                if completed == self.__COMPLETED_TRUE:
                    self.__completion.edge_search = True
                    self.__completion.web_search = True
                    self.__completion.mobile_search = True
                    self.__completion.offers = True
                    self.__completion.punchcard = True
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
            else:
                self.__search_hist = []

        if not self.__completion.is_all_completed():
            # update hist with todays time stamp
            self.__run_hist.append(self.get_timestamp())
            if len(self.__run_hist) == self.__MAX_HIST_LEN:
                self.__run_hist = self.__run_hist[1:]

        return self.__completion

    def get_search_hist(self):
        return self.__search_hist

    def write(self, completion, search_hist):
        self.__completion.update(completion)
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
            failed = ', '.join(failed)
            msg = self.__COMPLETED_FALSE.format(failed)
        else:
            msg = self.__COMPLETED_TRUE

        if self.__COMPLETED_TRUE not in self.__run_hist[-1]:
            self.__run_hist[-1] = "{}: {}".format(self.__run_hist[-1], msg)

        with open(self.run_path, "w") as log:
            log.write("\n".join(self.__run_hist) + "\n")

        if search_hist:
            for query in search_hist:
                if query not in self.__search_hist:
                    self.__search_hist.append(query)
            #to avoid UnicodeEncodeErrors
            self.__search_hist = [
                hist.encode('ascii', 'ignore').decode('ascii')
                for hist in self.__search_hist
            ]
            with open(self.search_path, "w") as log:
                log.write("\n".join(self.__search_hist) + "\n")


class Completion:
    def __init__(self):
        self.edge_search = False
        self.web_search = False
        self.mobile_search = False
        self.offers = False
        self.punchcard = False

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

    def is_web_device_completed(self):
        """ These searches require web driver """
        return self.web_search and self.offers and self.punchcard

    def is_all_completed(self):
        return self.is_edge_and_web_search_completed(
        ) and self.mobile_search and self.offers and self.punchcard

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

    def is_search_type_completed(self, search_type):
        if search_type == 'web':
            return self.is_edge_and_web_search_completed()
        elif search_type == 'mobile':
            return self.is_edge_and_mobile_search_completed()
        elif search_type == 'both':
            return self.is_both_searches_completed()
        elif search_type == 'offers':
            return self.is_offers_completed()
        elif search_type == 'punch card':
            return self.is_punchcard_completed()
        elif search_type in ('all', 'remaining'):
            return self.is_all_completed()


class BaseJsonLog:
    DATETIME_FORMAT = "%a, %b %d %Y %I:%M%p"
    LOCAL_TIMEZONE = tz.tzlocal()

    def __init__(self, log_path, run_datetime=datetime.now()):
        self.log_path = log_path
        self.run_datetime = run_datetime.replace(tzinfo=self.LOCAL_TIMEZONE)
        self.__read()

    def __read(self):
        if not os.path.exists(self.log_path):
            self.data = {}
        else:
            with open(self.log_path, ) as f:
                self.data = json.load(f)


class StatsJsonLog(BaseJsonLog):
    MAX_SIZE = 300

    def __init__(self, log_path):
        super().__init__(log_path)

    def write(self, stats_obj, email):
        stats_str = stats_obj.stats_str
        log_time = self.run_datetime.strftime(self.DATETIME_FORMAT)
        latest_log_entry = f'{log_time}: {"; ".join(stats_str)}'
        if email in self.data:
            self.data[email].append(latest_log_entry)
            self.data[email] = self.data[email][-self.MAX_SIZE:]
        else:
            self.data[email] = [latest_log_entry]

        with open(self.log_path, "w") as f:
            json.dump(self.data, f, indent=4, sort_keys=True)
