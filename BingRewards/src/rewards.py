from src.driver import ChromeDriverFactory
from src.log import Completion
import requests
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException, UnexpectedAlertPresentException, JavascriptException
import time
import sys
import re
import random
from datetime import datetime, timedelta, date
import json
import traceback
import locale


class Rewards:
    __LOGIN_URL = "https://login.live.com/"
    __BING_URL = "https://bing.com"
    __DASHBOARD_URL = "https://rewards.microsoft.com/"

    __WEB_DRIVER_WAIT_LONG = 30
    __WEB_DRIVER_WAIT_SHORT = 5

    __SYS_OUT_TAB_LEN = 8
    __SYS_OUT_PROGRESS_BAR_LEN = 30
    cookieclearquiz = 0
    _ON_POSIX = 'posix' in sys.builtin_module_names

    def __init__(self, email, password, debug=True, headless=True, cookies=False, driver_factory=ChromeDriverFactory):
        self.email = email
        self.password = password
        self.debug = debug
        self.headless = headless
        self.cookies = cookies
        self.completion = Completion()
        self.stdout = []
        self.search_hist = []
        self.__queries = []
        self.driver_factory = driver_factory

    def __get_sys_out_prefix(self, lvl, end):
        prefix = " " * (self.__SYS_OUT_TAB_LEN * (lvl - 1) - (lvl - 1))
        if not end:
            return prefix + ">" * lvl + " "
        else:
            return prefix + " " * int(
                self.__SYS_OUT_TAB_LEN / 2
            ) + "<" * lvl + " "

    def __sys_out(self, msg, lvl, end=False, flush=False):
        #to avoid UnicodeEncodeErrors
        msg = msg.encode('ascii', 'ignore').decode('ascii')
        if self.debug:
            if flush:  # because of progress bar
                print("")
            out = "{0}{1}{2}".format(
                self.__get_sys_out_prefix(lvl, end), msg,
                "\n" if lvl == 1 and end else ""
            )
            print(out)
            if len(self.stdout) > 0 and self.stdout[-1].startswith("\r"):
                self.stdout[-1] = self.stdout[-1][2:]
            self.stdout.append(out)

    def __sys_out_progress(self, current_progress, complete_progress, lvl):
        if self.debug:
            ratio = float(current_progress) / complete_progress
            current_bars = int(ratio * self.__SYS_OUT_PROGRESS_BAR_LEN)
            needed_bars = self.__SYS_OUT_PROGRESS_BAR_LEN - current_bars
            out = "\r{0}Progress: [{1}] {2}/{3} ({4}%)".format(
                self.__get_sys_out_prefix(lvl, False),
                "#" * current_bars + " " * needed_bars, current_progress,
                complete_progress, int(ratio * 100)
            )
            sys.stdout.write(out)
            sys.stdout.flush()
            if self.stdout[-1].startswith(
                "\r"
            ):  # dont need to check size of array before accessing element because progress never comes first
                self.stdout[-1] = out
            else:
                self.stdout.append(out)

    def __check_login_url(self, url):
        #made it to the home page! login complete
        if "https://account.microsoft.com/" in url:
            return True

        elif "https://login.live.com/ppsecure" in url:
            # approve sign in page
            try:
                WebDriverWait(self.driver, .5).until(
                    EC.element_to_be_clickable((By.ID, 'idChkBx_SAOTCAS_TD'))
                ).click()
                self.__sys_out("Waiting for user to approve sign-in request. In Microsoft Authenticator, please select approve.", 2)

            except TimeoutException:
                pass

            #'stay signed in' page
            finally:
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.ID, 'KmsiCheckboxField'))
                    ).click()
                except TimeoutException:
                    print('\nIssue logging in, please run in -nhl mode to see the problem\n')
                    raise
                #yes, stay signed in
                self.driver.find_element(By.XPATH, '//*[@id="idSIButton9"]').click()

        #'agree to terms and conditions' page
        elif "https://account.live.com/tou" in url:
            WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(
                EC.url_contains("https://account.live.com/tou")
            )
            WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.ID, 'iNext'))
            ).click()

        #'confirm identity' or 'recover account' page
        elif "identity/confirm" in url or "/recover" in url:
            raise RuntimeError(
                "Must confirm account identity by signing in manually first. Please login again with your Microsoft account in Google Chrome."
            )

        # 2FA page: login url doesn't change
        elif url == self.__LOGIN_URL:
            # standard 2FA page
            try:
                authenticator_code = self.driver.find_element(By.ID, "idRemoteNGC_DisplaySign").text
                self.__sys_out(f"Waiting for user to approve 2FA, please select {authenticator_code} in Microsoft Authenticator", 2)
                WebDriverWait(self.driver, 30).until(
                    EC.url_contains("https://login.live.com/ppsecure")
                    )
            except NoSuchElementException:
                raise RuntimeError(f"Unable to handle {url}")
            except TimeoutException:
                raise TimeoutException("You did not select code within Microsoft Authenticator in time.")

        else:
            raise RuntimeError("Made it to an unrecognized page during login process.")
        # login process not complete yet
        return False

    def __login(self):
        self.__sys_out("Logging in", 2)

        self.driver.get(self.__LOGIN_URL)
        ActionChains(self.driver).send_keys(
            self.email, Keys.RETURN
        ).perform()

        #login with credentials
        try:
            WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(
                EC.visibility_of_element_located((By.ID, "i0118"))
            ).send_keys(self.password, Keys.RETURN)
        except:
            ActionChains(self.driver).send_keys(
                self.password, Keys.RETURN
            ).perform()

        is_login_complete = False
        while not is_login_complete:
            time.sleep(1)
            is_login_complete = self.__check_login_url(self.driver.current_url)

        self.__sys_out("Successfully logged in", 2, True)
        VALID_MARKETS = ['mkt=EN-US', 'mkt=EN-GB', 'mkt=FR-FR', 'mkt=ES-ES', 'mkt=EN-AU', 'mkt=ZH-CN', 'mkt=IT-IT', 'mkt=DE-DE']
        if all(market not in self.driver.current_url for market in VALID_MARKETS):
            raise RuntimeError(
                f"Logged in, but user not located in one of these valid markets: {VALID_MARKETS}."
            )

    def __open_dashboard(self, try_count=0):
        """
        Opens dashboard url
        Checks that the url is correct
        And all the offer elements are loaded
        """
        max_try_count = 2
        self.driver.get(self.__DASHBOARD_URL)

        try:
            #check the url
            WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(
                # 'any_of' checks for either condition
                EC.any_of(
                    EC.url_contains("https://rewards.microsoft.com/?redref"),
                    EC.url_contains("https://rewards.microsoft.com/")
                )
            )
            # need to sign in via welcome page first
            if 'welcome' in self.driver.current_url:
                self.driver.find_element(By.XPATH, '//*[@id="raf-signin-link-id"]').click()

            #wait for offers to load completely
            offer_xpath = '//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[1]/div/card-content/mee-rewards-daily-set-item-content/div/a'
            WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.presence_of_element_located((By.XPATH, offer_xpath)))
        except (TimeoutException, NoSuchElementException) as e:
            if try_count == max_try_count:
                raise(e)
            self.__open_dashboard(try_count + 1)

    def find_between(self, s: str, first: str, last: str) -> str:
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""

    def get_dashboard_data(self):
        max_try_count = 3
        for try_count in range(1, max_try_count + 1):
            self.__open_dashboard()
            dashboard = self.find_between(
                self.driver.find_element(By.XPATH, '/html/body').get_attribute('innerHTML'),
                "var dashboard = ",
                ";\n        appDataModule.constant(\"prefetchedDashboard\", dashboard);"
            )
            try:
                dashboard = json.loads(dashboard)
                return dashboard
            except (json.decoder.JSONDecodeError, ValueError):
                print(f'\nJSONDecodeError try_count {try_count}')
                if try_count == (max_try_count):
                    raise

    def __get_search_progress(self, search_type):
        if len(self.driver.window_handles) == 1:  # open new tab
            self.driver.execute_script('window.open("");')
        self.driver.switch_to_last_tab()

        user_status = self.get_dashboard_data()['userStatus']
        counters = user_status['counters']

        if search_type == 'edge':
            search_key = 'pcSearch'
            search_index = 1
        elif search_type == 'web':
            search_key = 'pcSearch'
            search_index = 0
        elif search_type == 'mobile':
            search_key = 'mobileSearch'
            search_index = 0
            if user_status['levelInfo']['activeLevel'] == 'Level1':
                self.__sys_out("Account is 'LEVEL 1' - mobile searches not yet available.", 2, True)
                return False

        current_progress = counters[search_key][search_index]['pointProgress']
        complete_progress = counters[search_key][search_index]['pointProgressMax']

        self.driver.switch_to_first_tab()
        return current_progress, complete_progress

    def __update_search_queries(self, last_request_time):
        if last_request_time:
            time.sleep(
                max(
                    0, 20 - (datetime.now() - last_request_time).total_seconds()
                )
            )  # sleep at least 20 seconds to avoid over requesting server

        if self._ON_POSIX and locale.getlocale()[0] is not None:
            (lang, geo) = locale.getlocale()[0].split("_")  # en and US
        else:
            lang = "en"
            geo = "US"

        trends_url = "https://trends.google.com/trends/api/dailytrends"

        search_terms = set()
        trends_dict = {
            "hl": lang,
            "ed": str(
                (date.today() - timedelta(days=random.randint(1, 20))).strftime(
                    "%Y%m%d"
                )
            ),
            "geo": geo,
            "ns": 15,
        }

        req = requests.get(trends_url, params=trends_dict)
        google_trends = json.loads(req.text[6:])
        for topic in google_trends["default"]["trendingSearchesDays"][0][
            "trendingSearches"
        ]:
            search_terms.add(topic["title"]["query"].lower())
            for related_topic in topic["relatedQueries"]:
                search_terms.add(related_topic["query"].lower())
        search_terms = list(search_terms)
        random.shuffle(search_terms)
        self.__queries = search_terms

        last_request_time = datetime.now()
        return last_request_time

    def __search(self, search_type):

        def clean_query(query):
            #chromedriver 98+, special characters fail
            query = re.sub(r"[^a-zA-Z0-9\s]", "", query)
            #avoid UnicodeEncodeError when later writing to log
            query = query.encode('ascii', 'ignore').decode('ascii')
            return query

        self.__sys_out("Starting search", 2)
        self.driver.get(self.__BING_URL)

        cookieclear = 0
        prev_progress = -1
        try_count = 0

        last_request_time = None
        if len(self.__queries) == 0:
            last_request_time = self.__update_search_queries(
                last_request_time
            )
        while True:
            progress = self.__get_search_progress(search_type)
            if not progress:
                return False
            else:
                current_progress, complete_progress = progress
            if complete_progress > 0:
                self.__sys_out_progress(current_progress, complete_progress, 3)
            if current_progress == complete_progress:
                break
            elif current_progress == prev_progress:
                try_count += 1
                self.driver.refresh()
                if try_count == 4:
                    self.__sys_out("Failed to complete search", 2, True, True)
                    return False
                # handle mobile blank search-bar bug
                elif try_count >= 2:
                    self.driver.refresh()
                    time.sleep(2)
            else:
                prev_progress = current_progress
                try_count = 0

            search_box = WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.ID, "sb_form_q")))
            search_box.clear()

            # send query
            while True:
                if len(self.__queries) > 0:
                    query = self.__queries[0]
                    self.__queries = self.__queries[1:]
                else:
                    last_request_time = self.__update_search_queries(
                        last_request_time
                    )
                    continue
                if query not in self.search_hist:
                    break

            query = clean_query(query)
            search_box.send_keys(query, Keys.RETURN)  # unique search term
            self.search_hist.append(query)
            time.sleep(random.uniform(2, 4.5))

            if cookieclear == 0:
                try:
                    WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(
                        EC.element_to_be_clickable((By.ID, "bnp_btn_accept"))
                    ).click()
                except TimeoutException:
                    pass
                cookieclear = 1

            self.__handle_alerts()
        self.__sys_out("Successfully completed search", 2, True, True)
        return True

    def __get_quiz_progress(self, try_count=0):
        try:
            questions = self.driver.find_elements(By.XPATH,
                '//*[starts-with(@id, "rqQuestionState")]'
            )
            if len(questions) > 0:
                current_progress, complete_progress = 0, len(questions)
                for question in questions:
                    if question.get_attribute("class") == "filledCircle":
                        current_progress += 1
                    else:
                        break
                return current_progress - 1, complete_progress
            else:
                footer = self.driver.find_element(By.XPATH,
                    '//*[@id="FooterText0"]'
                ).text
                current_progress = footer[0]
                complete_progress = footer[-1]
                return current_progress, complete_progress

        except:
            if try_count < 4:
                return self.__get_quiz_progress(try_count + 1)
            else:
                return 0, -1

    def __start_quiz(self):
        # check for cookies
        try:
            WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(
                EC.element_to_be_clickable((By.ID, "bnp_btn_accept"))
            ).click()
        except TimeoutException:
            pass

        try_count = 0
        while True:
            try:
                start_quiz = WebDriverWait(
                    self.driver, self.__WEB_DRIVER_WAIT_SHORT
                ).until(
                    EC.visibility_of_element_located((By.ID, 'rqStartQuiz'))
                )
            #if quiz doesn't have a rStartQuiz element, it doesn't need to be prepped
            except TimeoutException:
                return True
            if start_quiz.is_displayed():
                try:
                    start_quiz.click()
                except:
                    self.driver.refresh()
                    time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
            else:
                try:
                    if self.driver.find_element(By.ID,
                        "quizWelcomeContainer"
                    ).get_attribute("style") == "display: none;":  # started
                        self.__sys_out("Successfully started quiz", 3, True)
                        break
                except:
                    self.driver.refresh()
                    time.sleep(self.__WEB_DRIVER_WAIT_SHORT)

            try_count += 1
            if try_count == 3:
                self.__sys_out("Failed to start quiz", 3, True)
                return False
            time.sleep(3)

        return True

    def __multiple_answers(self):
        """
        A type of quiz with overlay that have multple questions (usually 3), and within each question, the user must select x amount of correct answers (usually 5). Examples of this type of question are warpspeed and supersonic quizzes
        """
        while True:
            quiz_current_progress, quiz_complete_progress = self.__get_quiz_progress()
            self.__sys_out_progress(
                quiz_current_progress, quiz_complete_progress, 4
            )
            #either on the last question, or just completed
            if quiz_current_progress == quiz_complete_progress - 1:
                try:
                    time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                    #quiz has been completed
                    if len(
                        self.driver.find_elements(By.CLASS_NAME, 'headerMessage_Refresh')
                    ) > 0:
                        self.__sys_out_progress(
                            quiz_complete_progress, quiz_complete_progress, 4
                        )
                        self.__sys_out("Quiz complete", 3, True)
                        return True

                #just got to last question, time to solve it
                except:
                    pass

            #within the question, select the correct multiple answers
            try:
                option_index = 0
                question_progress = '0/5'
                question_progresses = [question_progress]
                while True:
                    if (
                        len(
                            self.driver.find_elements(
                                By.ID, 'rqAnswerOption{0}'.format(option_index)
                            )
                        )
                        <= 0
                    ):
                        return False
                    #find_element_by_id returns an EventFiringWebElement object, to get the web element, must use wrapped_element attribute
                    element = self.driver.find_element(By.ID,
                        'rqAnswerOption{0}'.format(option_index)
                    ).wrapped_element
                    #must use ActionChains due to error 'element is not clickable at point', for more info see this link:https://stackoverflow.com/questions/11908249/debugging-element-is-not-clickable-at-point-error
                    ActionChains(self.driver).move_to_element(element).click(
                        element
                    ).perform()
                    time.sleep(random.uniform(1, 4))
                    prev_progress = question_progress
                    #returns a string like '1/5' (1 out of 5 answers selected correctly so far)
                    question_progress = self.driver.find_element(By.CLASS_NAME,
                        'bt_corOpStat'
                    ).text
                    #once the last correct answer is clicked, question progress becomes '' or 5/5, tho in the past it became '0/5' sometimes, hence 2nd cond
                    if question_progress in ['', '5/5'] or (
                        prev_progress != question_progress
                        and question_progress in question_progresses
                    ):
                        #wait for the next question to appear
                        time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                        break
                    question_progresses.append(question_progress)
                    option_index += 1
            except:
                return False

    def __solve_tot(self):
        """
        Solves This or That quiz
        Logic to always get correct answer is from:
        https://github.com/charlesbel/Microsoft-Rewards-Farmer/blob/master/ms_rewards_farmer.py#L439
        """
        def get_answer_code(key, title):
            t = sum(ord(title[i]) for i in range(len(title)))
            t += int(key[-2:], 16)
            return str(t)

        try_count = 0
        while True:
            try:
                progress = WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_element_located((By.CLASS_NAME, 'bt_Quefooter'))).text
                current_question, complete_progress = map(
                    int, progress.split(' of ')
                )
                self.__sys_out_progress(current_question - 1, complete_progress, 4)

                answer_encode_key = self.driver.execute_script("return _G.IG")

                answer1 = self.driver.find_element(By.ID, "rqAnswerOption0")
                answer1_title = answer1.get_attribute('data-option')
                answer1_code = get_answer_code(answer_encode_key, answer1_title)

                answer2 = self.driver.find_element(By.ID, "rqAnswerOption1")

                correct_answer_code = self.driver.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")

                if answer1_code == correct_answer_code:
                    answer1.click()
                else:
                    answer2.click()

                time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                if current_question == complete_progress:
                    try:
                        header = WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_element_located((By.CLASS_NAME, 'headerMessage_Refresh')))
                        if "you earned" in header.text.lower():
                            self.__sys_out_progress(
                                complete_progress, complete_progress, 4
                            )
                            return True
                    #the header message could not be found
                    except TimeoutException:
                        return False
            except:
                try_count += 1
                if try_count >= 2:
                    self.__sys_out(
                        "Failed to complete This or That quiz due to following exception:", 3, True, True
                    )
                    error_msg = traceback.format_exc()
                    self.__sys_out(error_msg, 3)
                    return False

    def __solve_hot_take(self):
        try:
            self.driver.find_element(By.ID,
                'btoption{}'.format(random.choice(([0, 1])))
            ).click()
            return True
        except TimeoutException:
            self.__sys_out("Failed to complete Hot Takes", 3, True, True)
            return False

    def __quiz(self):
        started = self.__start_quiz()
        if not started:
            return started

        quiz_options_len = 4
        is_drag_and_drop = False
        is_tot = False
        is_hot_take = False
        is_multiple_answers = False

        if len(self.driver.find_elements(By.ID, 'rqAnswerOptionNum0')) > 0:
            is_drag_and_drop = True
            self.__sys_out("Drag and drop", 3)
        elif len(self.driver.find_elements(By.CLASS_NAME, 'btCorOps')) > 0:
            is_multiple_answers = True
            self.__sys_out("Multiple Answers", 3)
        elif len(self.driver.find_elements(By.CLASS_NAME, 'btOptionAnsOvl')) > 0:
            is_tot = True
        elif len(self.driver.find_elements(By.ID, 'btPollOverlay')) > 0:
            is_hot_take = True
        else:
            self.__sys_out("Multiple choice", 3)

        # drag and drop
        if is_drag_and_drop:
            time.sleep(self.__WEB_DRIVER_WAIT_SHORT)  # let demo complete

            # get all possible combinations
            to_from_combos = []
            for from_index in range(quiz_options_len):
                for to_index in range(quiz_options_len):
                    if from_index != to_index:
                        to_from_combos.append((from_index, to_index))

            prev_progress = -1
            incorrect_options = []
            from_option_index, to_option_index = -1, -1
            while True:
                current_progress, complete_progress = self.__get_quiz_progress()
                if complete_progress > 0:
                    self.__sys_out_progress(
                        current_progress, complete_progress, 4
                    )

                # get all correct combinations so to not use them again
                correct_options = []
                option_index = 0
                while option_index < quiz_options_len:
                    try:
                        option = WebDriverWait(
                            self.driver, self.__WEB_DRIVER_WAIT_LONG
                        ).until(
                            EC.visibility_of_element_located(
                                (
                                    By.ID,
                                    "rqAnswerOption{0}".format(option_index)
                                )
                            )
                        )
                        if option.get_attribute(
                            "class"
                        ) == "rqOption rqDragOption correctAnswer":
                            correct_options.append(option_index)
                        option_index += 1
                    except TimeoutException:
                        self.__sys_out("Time out Exception", 3)
                        return False

                if current_progress != prev_progress:  # new question
                    incorrect_options = []
                    prev_progress = current_progress
                else:
                    # update incorrect options
                    incorrect_options.append(
                        (from_option_index, to_option_index)
                    )
                    incorrect_options.append(
                        (to_option_index, from_option_index)
                    )

                exit_code = -1  # no choices were swapped
                for combo in to_from_combos:
                    from_option_index, to_option_index = combo[0], combo[1]
                    # check if combination has already been tried
                    if combo not in incorrect_options and from_option_index not in correct_options and to_option_index not in correct_options:
                        # drag from option to to option
                        from_option = WebDriverWait(
                            self.driver, self.__WEB_DRIVER_WAIT_LONG
                        ).until(
                            EC.visibility_of_element_located(
                                (
                                    By.ID, "rqAnswerOption{0}".
                                    format(from_option_index)
                                )
                            )
                        )
                        to_option = WebDriverWait(
                            self.driver, self.__WEB_DRIVER_WAIT_LONG
                        ).until(
                            EC.visibility_of_element_located(
                                (
                                    By.ID,
                                    "rqAnswerOption{0}".format(to_option_index)
                                )
                            )
                        )
                        ActionChains(self.driver).drag_and_drop(
                            from_option, to_option
                        ).perform()
                        time.sleep(self.__WEB_DRIVER_WAIT_SHORT)

                        if current_progress == complete_progress - 1:  # last question
                            try:
                                header = WebDriverWait(
                                    self.driver, self.__WEB_DRIVER_WAIT_SHORT
                                ).until(
                                    EC.visibility_of_element_located(
                                        (
                                            By.XPATH,
                                            '//*[@id="quizCompleteContainer"]/div'
                                        )
                                    )
                                )
                                #if header.text == "Way to go!":
                                if "great job" in header.text.lower():
                                    self.__sys_out_progress(
                                        complete_progress, complete_progress, 4
                                    )
                                    exit_code = 0  # successfully completed
                                    break
                            except:
                                pass
                        exit_code = 1  # successfully swapped 2 choices (can still be wrong)
                        break

                if exit_code == -1:
                    self.__sys_out(
                        "Failed to complete quiz1- drag and drop - tried every choice", 3,
                        True, True
                    )
                    return False
                elif exit_code == 0:
                    break

        #multiple answers per question (i.e. warp speed/supersonic)
        elif is_multiple_answers:
            return self.__multiple_answers()

        #this or that quiz
        elif is_tot:
            return self.__solve_tot()

        elif is_hot_take:
            return self.__solve_hot_take()

        # multiple choice (i.e. lignting speed)
        else:
            prev_progress = -1
            prev_options = []
            try_count = 0
            prev_complete_progress = 0  # complete progress becomes 0 at end of quiz, for printing purposes
            while True:
                current_progress, complete_progress = self.__get_quiz_progress()
                if complete_progress > 0:
                    #selected the correct answer
                    if current_progress != prev_progress:
                        self.__sys_out_progress(
                            current_progress, complete_progress, 4
                        )
                        prev_progress = current_progress
                        prev_options = []
                        try_count = 0
                        prev_complete_progress = complete_progress
                else:
                    try_count += 1
                    if try_count == quiz_options_len:
                        self.__sys_out(
                            "Failed to complete quiz1 - no progress", 3, True,
                            True
                        )
                        return False

                if current_progress == complete_progress - 1:  # last question, works for -1, 0 too (already complete)
                    try:
                        header = WebDriverWait(
                            self.driver, self.__WEB_DRIVER_WAIT_SHORT
                        ).until(
                            EC.visibility_of_element_located(
                                (
                                    By.XPATH,
                                    '//*[@id="quizCompleteContainer"]/div'
                                )
                            )
                        )
                        #if header.text == "Way to go!":
                        finish_msg = header.text.lower()
                        if "you earned" in finish_msg or 'great job' in finish_msg:
                            if prev_complete_progress > 0:
                                self.__sys_out_progress(
                                    prev_complete_progress,
                                    prev_complete_progress, 4
                                )
                                break
                            else:
                                self.__sys_out(
                                    "Already completed quiz", 3, True
                                )
                                return True
                    except:
                        pass

                # select choice
                for option_index in range(quiz_options_len):
                    if option_index not in prev_options:
                        break
                if option_index in prev_options:
                    self.__sys_out(
                        "Failed to complete quiz1 multiple choice - tried every choice", 3,
                        True, True
                    )
                    return False

                try:
                    # click choice
                    WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_LONG).until(
                        EC.element_to_be_clickable(
                            (By.ID, "rqAnswerOption{0}".format(option_index))
                        )
                    ).click()
                    prev_options.append(option_index)
                    time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                except TimeoutException:
                    self.__sys_out("Time out Exception", 3)
                    return False

        self.__sys_out("Successfully completed quiz", 3, True, True)
        return True

    def __quiz2(self):
        self.__sys_out("Starting quiz2 (no overlay)", 3)
        current_progress, complete_progress = 0, -1

        while current_progress != complete_progress:
            try:
                progress = WebDriverWait(
                    self.driver, self.__WEB_DRIVER_WAIT_SHORT
                ).until(
                    EC.visibility_of_element_located(
                        (
                            By.XPATH, '//*[@id="QuestionPane{}"]/div[2]'.
                            format(current_progress)
                        )
                    )
                ).text
            except TimeoutException:
                self.__sys_out("Could not find quiz2 progress elements", 3)
                return False
            try:
                #capture quiz progress
                current_progress, complete_progress = [
                    int(x)
                    for x in re.match("\((\d+)[a-zA-Z ]+(\d+)\)", progress).groups()
                ]
            except AttributeError:
                self.__sys_out("Skipping quiz, issue with regex identifying progress, most likely non-English site.", 3)
                return False
            self.__sys_out_progress(current_progress - 1, complete_progress, 4)
            time.sleep(random.uniform(1, 3))
            self.driver.find_elements(By.CLASS_NAME, 'wk_Circle')[random.randint(
                0, 2
            )].click()
            time.sleep(self.__WEB_DRIVER_WAIT_SHORT)

            is_clicked, try_count = False, 0
            #sometimes the 'next' button isn't clickable and page needs to be refreshed
            while not is_clicked:
                if len(self.driver.find_elements(By.CLASS_NAME, 'cbtn')) > 0:
                    WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, 'cbtn'))
                    ).click()
                elif len(self.driver.find_elements(By.CLASS_NAME, 'wk_button')) > 0:
                    WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(
                        EC.element_to_be_clickable(
                            (By.CLASS_NAME, 'wk_button')
                        )
                    ).click()
                elif len(self.driver.find_elements(By.ID, 'check')) > 0:
                    WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(
                        EC.element_to_be_clickable((By.ID, 'check'))
                    ).click()
                else:
                    self.__sys_out("Failed to complete quiz2", 3, True, True)
                    return False

                try:
                    if current_progress != complete_progress:
                        WebDriverWait(self.driver, 5).until(
                            EC.visibility_of_element_located(
                                (
                                    By.XPATH,
                                    '//*[@id="QuestionPane{}"]/div[2]'.
                                    format(current_progress)
                                )
                            )
                        ).text
                    is_clicked = True

                except:
                    #implies one of the next buttons was found, but wasn't able to click it
                    self.driver.refresh()
                    try_count += 1
                    if try_count == 2:
                        self.__sys_out(
                            "Quiz2 element not clickable", 3, True, True
                        )
                        return False

        #if current_progress == complete_progress:
        self.__sys_out_progress(current_progress, complete_progress, 4)
        self.__sys_out("Successfully completed quiz2", 3, True, True)
        return True

    def __poll(self, title):
        self.__sys_out("Starting poll", 3)
        time.sleep(self.__WEB_DRIVER_WAIT_SHORT)

        #for daily poll
        if 'daily' in title:
            element_id = 'btoption{0}'.format(random.randint(0, 1))
        #all other polls
        else:
            #xpath = '//*[@id="OptionText0{}"]'.format(random.randint(0, 1))
            element_id = 'OptionText0{0}'.format(random.randint(0, 1))

        try:
            WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(
                EC.element_to_be_clickable((By.ID, element_id))
            ).click()
            self.__sys_out("Successfully completed poll", 3, True)
            return True
        except TimeoutException:
            self.__sys_out("Failed to complete poll", 3, True)
            return False

    def __handle_alerts(self):
        """
        Handle any Bing location pop-up alerts
        """
        try:
            self.driver.switch_to.alert.dismiss()
        except (NoAlertPresentException, UnexpectedAlertPresentException):
            pass

    def __is_offer_sign_in_bug(self):
        """
        Sometimes when clicking an offer for the first time, it will show a page saying the user is not signed in. Pretty sure it's a Bing bug. This method checks for this bug
        """
        try:
            self.driver.find_element(By.CLASS_NAME, 'identityStatus')
            return True
        except NoSuchElementException:
            return False

    def __has_overlay(self):
        """
        most offers that have the word 'quiz' in title have a btOverlay ID. However, certain quizzes that related to special events i.e. halloween do not have this overlay
        """
        self.__sys_out("Starting quiz", 3)
        try_count = 0
        while True:
            try:
                self.driver.find_element(By.ID, "btOverlay")
                return True
            except NoSuchElementException:
                try_count += 1
                if try_count >= 1:
                    self.__sys_out("Could not detect quiz overlay", 3, True)
                    return False
                time.sleep(2)

    def __check_offer_status(self, offer):
        # check whether it was already completed
        checked = False
        try:
            checked_xpath = './mee-rewards-points/div/div/span[1]'
            icon = offer.find_element(By.XPATH, checked_xpath)
            if icon.get_attribute('class').startswith(
                "mee-icon mee-icon-SkypeCircleCheck"
            ):
                checked = True
        #quiz does not contain a check-mark icon, implying no points offered
        except NoSuchElementException:
            checked = True
        return checked

    def __click_offer(self, offer):
        title_xpath = './div[2]/h3'
        title = offer.find_element(By.XPATH, title_xpath).text
        self.__sys_out("Trying {0}".format(title), 2)

        completed = True
        checked = self.__check_offer_status(offer)

        if checked:
            self.__sys_out("Already completed, or no points offered", 2, True)

        else:
            offer.click()
            self.driver.switch_to_last_tab()
            #Check for cookies popup - UK thing
            if self.cookieclearquiz == 0:

                self.__sys_out("Checking cookies popup", 3)
                try:
                    WebDriverWait(self.driver, self.__WEB_DRIVER_WAIT_SHORT).until(
                        EC.element_to_be_clickable((By.ID, "bnp_btn_accept"))
                    ).click()
                    self.__sys_out("cookie popup cleared", 3)
                    self.cookieclearquiz = 1
                except TimeoutException:
                    self.__sys_out("No cookie popup present", 3)
                    self.cookieclearquiz = 1

            if self.__is_offer_sign_in_bug():
                completed = -1

            elif "poll" in title.lower():
                completed = self.__poll(title.lower())

            #if "quiz" in title.lower()
            else:
                if self.__has_overlay():
                    completed = self.__quiz()
                else:
                    completed = self.__quiz2()

            if completed == -1:
                self.__sys_out(
                    "Sign in Bing bug for offer '{0}', will try again".
                    format(title), 2, True
                )
            elif completed:
                self.__sys_out(
                    "Successfully completed '{0}'".format(title), 2, True
                )
            else:
                self.__sys_out("Failed to complete '{0}'".format(title), 2, True)

            self.driver.switch_to_first_tab()
            self.__open_dashboard()  # for stale element exception

        return completed

    def map_offers(self):
        """
        Creates a dictionary where (k, v)= (offer title, offer element)
        Useful for testing individual offers
        """
        self.__open_dashboard()
        title_to_offer = {}
        for i in range(3):
            offer = self.driver.find_element(By.XPATH,
                '//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{}]/div/card-content/mee-rewards-daily-set-item-content/div/a'
                .format(i + 1)
            )
            title = offer.find_element(By.XPATH, './div[2]/h3').text
            title_to_offer[title + str(i)] = offer

        for i in range(30):
            try:
                offer = self.driver.find_element(By.XPATH,
                    '//*[@id="more-activities"]/div/mee-card[{}]/div/card-content/mee-rewards-more-activities-card-item/div/a'
                    .format(i + 1)
                )
                title = offer.find_element(By.XPATH, './div[2]/h3').text
                title_to_offer[title + str(i)] = offer
                i += 1
            except NoSuchElementException:
                pass
        return title_to_offer

    def __perform_action_on_offers(self, action, offer_xpath, completed, offer_count):
        for i in range(offer_count):
            #always start on first tab in case prev offer errored out
            self.driver.switch_to_first_tab()
            self.driver.close_other_tabs()
            offer = self.driver.find_element(By.XPATH,
                offer_xpath.format(offer_index=i + 1)
            )

            # don't crash program if an offer fails
            try:
                c = action(offer)
                # sign in bug- try one more time
                if c == -1:
                    #need to reobtain element, else stale
                    offer = self.driver.find_element(By.XPATH,
                        offer_xpath.format(offer_index=i + 1)
                    )
                    c = action(offer)
                completed.append(c)
            except (NoSuchElementException, TimeoutException):
                error_msg = traceback.format_exc()
                self.__sys_out(f'Exception for this offer, proceeding to next one:\n{error_msg}', 1)

    def __offers(self):
        # showcase offer
        self.__open_dashboard()

        #daily set
        daily_sets_xpath = '//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{offer_index}]/div/card-content/mee-rewards-daily-set-item-content/div/a'
        self.__perform_action_on_offers(self.__click_offer, daily_sets_xpath, [], offer_count=3)

        # remaining offers
        remaining_offer_count = len(self.driver.find_elements(By.XPATH,
            '//*[@id="more-activities"]/div/mee-card'
        ))
        more_activities_xpath = '//*[@id="more-activities"]/div/mee-card[{offer_index}]/div/card-content/mee-rewards-more-activities-card-item/div/a'
        self.__perform_action_on_offers(self.__click_offer, more_activities_xpath, [], offer_count=remaining_offer_count)

        completed = []
        # check offers status after all offers have been tried
        self.__perform_action_on_offers(self.__check_offer_status, daily_sets_xpath, completed, offer_count=3)
        self.__perform_action_on_offers(self.__check_offer_status, more_activities_xpath, completed, offer_count=remaining_offer_count)

        return min(completed)

    def __punchcard_activity(self, parent_url, childPromotions):
        """
        Each punch card has multiple activities.
        Completes the latest punch card activity.
        """
        for activity_index, activity in enumerate(childPromotions):
            if activity['complete'] is False:
                activity_title = activity['title']
                self.__sys_out(f'Starting activity "{activity_title}"', 2)
                if activity['promotionType'] == "quiz":
                    activity_url = activity['attributes']['destination']
                    #can't use redirect link b/c it disappears if you want to start a quiz that was already in progress
                    self.driver.get(activity_url)
                    time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                    if self.__is_offer_sign_in_bug():
                        self.__sys_out(
                            f"Sign in Bing bug for offer '{activity_title}', will try again", 2, True
                        )
                        self.driver.get(activity_url)

                    if self.__has_overlay():
                        self.__quiz()
                    else:
                        self.__quiz2()

                elif activity['promotionType'] == "urlreward":
                    self.driver.get(parent_url)
                    time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                    #reached error page
                    if 'error' in self.driver.current_url:
                        self.__sys_out('Reached error page', 3, end=True)
                        return activity_index

                    try:
                        #will only get points if you click the redirect link, can't go to the page directly
                        self.driver.execute_script("document.getElementsByClassName('offer-cta')[0].click()")
                    #most likely target page was not opened, except clause so program can continue to mobile
                    except JavascriptException:
                        return activity_index
                    time.sleep(2)
                    self.driver.close()
                    self.driver.switch_to_first_tab()

                #stop after completing one activity
                break
        # return the activity number so we can get it's progress later
        return activity_index

    def __punchcard(self):
        is_complete_activity = True
        has_valid_punch = False
        punchcards = self.get_dashboard_data()['punchCards']

        for punchcard_index, punchcard in enumerate(punchcards):
            valid_offer_types = ('quiz', 'urlreward')
            try:
                #get punch card offer types
                punchcard_offer_types = punchcard['parentPromotion']['attributes']['type'].split(',')
            except (KeyError, TypeError):
                punchcard_offer_types = [None]

            # Check if valid punchcard
            if punchcard.get('parentPromotion') \
            and all(punchcard_offer_type in valid_offer_types for punchcard_offer_type in punchcard_offer_types) \
            and punchcard['parentPromotion'].get('pointProgressMax', 0) != 0 \
            and punchcard.get('childPromotions'):
                has_valid_punch = True
                parent_url = punchcard['parentPromotion']['attributes']['destination']
                title = punchcard['parentPromotion']['attributes']['title']
                # check if valid punchcard is completed
                is_complete_punchcard = punchcard['parentPromotion']['complete']
                if not is_complete_punchcard:
                    self.__sys_out(f'Punch card "{title}" is not complete yet.', 2)
                    #complete latest punch card activity
                    activity_index = self.__punchcard_activity(parent_url, punchcard['childPromotions'])
                    is_complete_activity = self.get_dashboard_data()['punchCards'][punchcard_index]['childPromotions'][activity_index]['complete']
                    if is_complete_activity:
                        self.__sys_out('Latest punch card activity successfully completed!', 3)
                    else:
                        self.__sys_out('Latest punch card activity NOT successfully completed. Possibly not enough time has elapsed since last punch.', 3)
                else:
                    self.__sys_out(f'Punch card "{title}" is already completed.', 2)

        # no punchcards offered
        if not has_valid_punch:
            self.__sys_out('No valid punch cards offered', 3)
            return True

        self.driver.get(parent_url)
        punchcard_progress = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//div[@class='punchcard-completion-row']"))).text
        self.__sys_out(f'Overall punch card progress: {punchcard_progress}', 2)
        return is_complete_punchcard or is_complete_activity

    def __print_stats(self, init_points=0):
        try:
            # dashboard dictionary data
            dashboard = self.get_dashboard_data()
            user_d = dashboard['userStatus']
            streak_d = dashboard["streakBonusPromotions"][0]

            # get the values from the dictionary
            earned_today = user_d['counters']['dailyPoint'][0]['pointProgress']
            available_points = user_d['availablePoints']
            earned_now = available_points - init_points
            lifetime_points = user_d['lifetimePoints']
            streak_count = streak_d['activityProgress']

            #use xpath to get days till streak bonus
            user_level = user_d['levelInfo']['activeLevel']
            days_to_bonus_index = 3 if user_level == 'Level2' else 4
            days_to_bonus_str = self.driver.find_elements(
                By.XPATH, '//mee-rewards-counter-animation//span'
            )[days_to_bonus_index].text

            self.stats = RewardStats(
            earned_now, earned_today, streak_count, available_points,
            lifetime_points, days_to_bonus_str
            )

            self.__sys_out("Summary", 1, flush=True)
            for stat_str in self.stats.stats_str:
                if 'until bonus' in stat_str:
                    self.__sys_out(stat_str, 2, end=True)
                else:
                    self.__sys_out(stat_str, 2)

        except Exception:
            error_msg = traceback.format_exc()
            self.__sys_out(f'Error checking rewards status -\n {error_msg}', 1)

    def __get_driver(self, device_type):
        try:
            self.driver = self.driver_factory.get_driver(
                device_type, self.headless, self.cookies
            )
            self.__login()
        except:
            try:
                self.driver.quit()
            except AttributeError:  # not yet initialized
                pass
            raise

    def __get_available_points(self):
        return self.get_dashboard_data()['userStatus']['availablePoints']

    def __complete_action(self, action, description, mandatory_device_type=None, **action_kwargs):
        self.__sys_out(f"Starting {description}", 1)

        try:
            if mandatory_device_type and mandatory_device_type != self.driver.device:
                self.driver.quit()
                self.__get_driver(mandatory_device_type)
            completion = action(**action_kwargs)
            if completion:
                self.__sys_out(f"Successfully completed {description}", 1, True)
            else:
                self.__sys_out(f"Failed to complete {description}", 1, True)

        except (TimeoutException, NoSuchElementException):
            error_msg = traceback.format_exc()
            self.__sys_out(f'Error during {description}:\n {error_msg}', 1)
            return False

        except:
            try:
                self.driver.quit()
            except AttributeError:  # not yet initialized
                pass
            raise

        return completion

    def __complete_edge_search(self):
        action_kwargs = {'search_type': 'edge'}

        self.completion.edge_search = self.__complete_action(
            action=self.__search,
            description='Edge search',
            **action_kwargs
        )

    def __complete_web_search(self):
        action_kwargs = {'search_type': 'web'}

        self.completion.web_search = self.__complete_action(
            action=self.__search,
            description='Web search',
            mandatory_device_type=self.driver_factory.WEB_DEVICE,
            **action_kwargs
        )

    def __complete_mobile_search(self):
        action_kwargs = {'search_type': 'mobile'}

        self.completion.mobile_search = self.__complete_action(
            action=self.__search,
            description='Mobile search',
            mandatory_device_type=self.driver_factory.MOBILE_DEVICE,
            **action_kwargs
)

    def __complete_offers(self):
        self.completion.offers = self.__complete_action(
            action=self.__offers,
            description='Offers',
            # mobile driver offer links can be wonky
            mandatory_device_type=self.driver_factory.WEB_DEVICE,
        )

    def __complete_punchcard(self):
        self.completion.punchcard = self.__complete_action(
            action=self.__punchcard,
            description='punch card',
            #first punchcard is a quiz,must use web device
            mandatory_device_type=self.driver_factory.WEB_DEVICE
        )

    def complete_both_searches(self):
        self.__complete_edge_search()
        self.__complete_web_search()
        self.__complete_mobile_search()

    def complete_remaining_searches(self, search_type, prev_completion):
        is_search_all = search_type == 'all'

        if not prev_completion.is_edge_search_completed() or is_search_all:
            self.__complete_edge_search()
        if not prev_completion.is_web_search_completed() or is_search_all:
            self.__complete_web_search()
        if not prev_completion.is_offers_completed() or is_search_all:
            self.__complete_offers()
        if not prev_completion.is_punchcard_completed() or is_search_all:
            self.__complete_punchcard()
        if not prev_completion.is_mobile_search_completed() or is_search_all:
            self.__complete_mobile_search()

    def complete_search_type(self, search_type, prev_completion, search_hist):
        self.search_hist = search_hist

        if (search_type == 'mobile') or (prev_completion.is_web_device_completed()):
            device_type = self.driver_factory.MOBILE_DEVICE
        else:
            device_type = self.driver_factory.WEB_DEVICE

        self.__get_driver(device_type)
        init_points = self.__get_available_points()

        if search_type in ('remaining', 'all'):
            self.complete_remaining_searches(search_type, prev_completion)
        # if either web/mobile, check if edge is complete
        elif search_type in ('web', 'mobile'):
            if not prev_completion.is_edge_search_completed():
                self.__complete_edge_search()
            if search_type == 'web':
                self.__complete_web_search()
            else:
                self.__complete_mobile_search()
        elif search_type == 'offers':
            self.__complete_offers()
        elif search_type == 'punch card':
            self.__complete_punchcard()
        elif search_type == 'both':
            self.complete_both_searches()

        self.__print_stats(init_points)
        self.driver.quit()


class RewardStats:
    def __init__(
        self, earned_now, earned_today, streak_count, available_points,
        lifetime_points, days_to_bonus_str
    ):
        self.earned_now = earned_now
        self.earned_today = earned_today
        self.streak_count = streak_count
        self.available_points = available_points
        self.lifetime_points = lifetime_points
        self.days_to_bonus_str = days_to_bonus_str
        self.build_str()

    def build_str(self):
        # build strings for sys_out & Telegram
        self.earned_now_str = f'Points earned this run: {self.earned_now}'
        self.earned_today_str = f"Microsoft 'Points earned' today: {self.earned_today}"
        self.streak_count_str = f'Streak count: {self.streak_count}'
        self.available_points_str = f'Available points: {self.available_points:,}'
        self.lifetime_points_str = f'Lifetime points: {self.lifetime_points:,}'

        self.stats_str = [
            self.earned_now_str, self.earned_today_str, self.streak_count_str,
            self.days_to_bonus_str, self.available_points_str,
            self.lifetime_points_str
        ]
