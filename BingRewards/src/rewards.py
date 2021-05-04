from src.driver import Driver
from src.log import Completion
from urllib.request import urlopen
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException, ElementClickInterceptedException, StaleElementReferenceException
import base64
import time
import sys
import re
import random
from datetime import datetime, timedelta
import json
import ssl


class Rewards:
    __LOGIN_URL                 = "https://login.live.com"
    __BING_URL                  = "https://bing.com"
    __DASHBOARD_URL             = "https://account.microsoft.com/rewards/"
    __POINTS_URL                = "https://account.microsoft.com/rewards/pointsbreakdown"
    __TRENDS_URL                = "https://trends.google.com/trends/api/dailytrends?hl=en-US&ed={}&geo=US&ns=15"

    __WEB_DRIVER_WAIT_LONG      = 30
    __WEB_DRIVER_WAIT_SHORT     = 5

    __SYS_OUT_TAB_LEN           = 8
    __SYS_OUT_PROGRESS_BAR_LEN  = 30

    def __init__(self, path, email, password, debug=True, headless=True):
        self.path               = path
        self.email              = email
        self.password           = password
        self.debug              = debug
        self.headless           = headless
        self.completion         = Completion()
        self.stdout             = []
        self.search_hist        = []
        self.__queries          = []

    def __get_sys_out_prefix(self, lvl, end):
        prefix = " "*(self.__SYS_OUT_TAB_LEN*(lvl-1)-(lvl-1))
        if not end:
            return prefix + ">"*lvl + " "
        else:
            return prefix + " "*int(self.__SYS_OUT_TAB_LEN/2) + "<"*lvl + " "

    def __sys_out(self, msg, lvl, end=False, flush=False):
        #to avoid UnicodeEncodeErrors
        msg = msg.encode('ascii', 'ignore').decode('ascii')
        if self.debug:
            if flush: # because of progress bar
                print("")
            out = "{0}{1}{2}".format(self.__get_sys_out_prefix(lvl, end), msg, "\n" if lvl==1 and end else "")
            print(out)
            if len(self.stdout) > 0:
                if self.stdout[-1].startswith("\r"):
                    self.stdout[-1] = self.stdout[-1][2:]
            self.stdout.append(out)

    def __sys_out_progress(self, current_progress, complete_progress, lvl):
        if self.debug:
            ratio = float(current_progress)/complete_progress
            current_bars = int(ratio*self.__SYS_OUT_PROGRESS_BAR_LEN)
            needed_bars = self.__SYS_OUT_PROGRESS_BAR_LEN-current_bars
            out = "\r{0}Progress: [{1}] {2}/{3} ({4}%)".format(self.__get_sys_out_prefix(lvl, False), "#"*current_bars + " "*needed_bars,
                                                               current_progress, complete_progress, int(ratio*100))
            sys.stdout.write(out)
            sys.stdout.flush()
            if self.stdout[-1].startswith("\r"): # dont need to check size of array before accessing element because progress never comes first
                self.stdout[-1] = out
            else:
                self.stdout.append(out)

    def __login(self, driver):
        self.__sys_out("Logging in", 2)

        driver.get(self.__LOGIN_URL)
        ActionChains(driver).send_keys(base64.b64decode(self.email).decode(), Keys.RETURN).perform()
        try:
            WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.ID, "i0118"))).send_keys(base64.b64decode(self.password).decode(), Keys.RETURN)
        except:
            ActionChains(driver).send_keys(base64.b64decode(self.password).decode(), Keys.RETURN).perform()

        #stay signed in
        try:
            #don't show this again checkbox
            WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, 'KmsiCheckboxField'))).click()
            #yes, stay signed in
            driver.find_element_by_xpath('//*[@id="idSIButton9"]').click()
        except TimeoutException:
            pass

        #check login was sucessful
        try:
            WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.url_contains("https://account.microsoft.com/"))
            self.__sys_out("Successfully logged in", 2, True)
            VALID_MARKETS = ['mkt=EN-US', 'mkt=EN-GB']
            if not any(market in driver.current_url for market in VALID_MARKETS):
                raise RuntimeError("Logged in, but user not located in a valid market (USA, UK).")
        except:
            raise RuntimeError("Did NOT log in successfully")

    def __get_search_progress(self, driver, device, is_edge=False):
        if len(driver.window_handles) == 1: # open new tab
            driver.execute_script('''window.open("{0}");'''.format(self.__POINTS_URL))
        driver.switch_to.window(driver.window_handles[-1])
        driver.refresh()
        time.sleep(1)

        try_count = 0
        while True:
            try:
                progress_elements = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_all_elements_located((By.XPATH, '//*[@id="userPointsBreakdown"]/div/div[2]/div/div[*]')))
                break
            except TimeoutException:
                try_count += 1
                time.sleep(3)
            if try_count == 2:
                msg = 'When searching, too many time out exceptions when getting progress elements'
                self.__sys_out(msg, 3, True)
                raise NoSuchElementException(msg)

        if is_edge:
            search_type = 'EDGE'
        elif device == Driver.WEB_DEVICE:
            search_type = 'PC'
        elif device == Driver.MOBILE_DEVICE:
            search_type = 'MOBILE'

        progress_text = None
        for element in progress_elements:
            progress_name = element.find_element_by_xpath('./div/div[2]/mee-rewards-user-points-details/div/div/div/div/p[1]').text.upper()
            if search_type in progress_name:
                progress_text = element.find_element_by_xpath('./div/div[2]/mee-rewards-user-points-details/div/div/div/div/p[2]').text
                break

        if progress_text is None:
            msg = "Ending {search_type} search. Could not detect search progress.".format(search_type=search_type)
            if search_type == 'MOBILE':
                msg += "Most likely because user is at LEVEL 1 and mobile searches are unavailable."
            self.__sys_out(msg, 3, True)
            return False

        current_progress, complete_progress = [int(match) for match in re.findall('\d+', progress_text)]
        driver.switch_to.window(driver.window_handles[0])
        return current_progress, complete_progress

    def __update_search_queries(self, timestamp, last_request_time):
        if last_request_time:
            time.sleep(max(0, 20-(datetime.now()-last_request_time).total_seconds())) # sleep at least 20 seconds to avoid over requesting server
        try:
            response = urlopen(self.__TRENDS_URL.format(timestamp.strftime("%Y%m%d")), context=ssl.SSLContext(ssl.PROTOCOL_TLSv1))
        except ssl.SSLError as e:
            response = urlopen(self.__TRENDS_URL.format(timestamp.strftime("%Y%m%d")))

        last_request_time = datetime.now()
        output = response.read()[5:]
        if type(output) == bytes:
            output = output.decode('utf-8')
        response = json.loads(output)

        #self.__queries = [] # will already be empty
        for topic in response["default"]["trendingSearchesDays"][0]["trendingSearches"]:
            self.__queries.append(topic["title"]["query"].lower())
            for related_topic in topic["relatedQueries"]:
                self.__queries.append(related_topic["query"].lower())
        return last_request_time

    def __search(self, driver, device, is_edge=False):
        self.__sys_out("Starting search", 2)
        driver.get(self.__BING_URL)

        prev_progress = -1
        try_count = 0
        trending_date = datetime.now()

        last_request_time = None
        if len(self.__queries) == 0:
            last_request_time = self.__update_search_queries(trending_date, last_request_time)
        while True:
            progress = self.__get_search_progress(driver, device, is_edge)
            if progress == False:
                return False
            else:
                current_progress, complete_progress = progress
            if complete_progress > 0:
                self.__sys_out_progress(current_progress, complete_progress, 3)
            if current_progress == complete_progress:
                break
            elif current_progress == prev_progress:
                try_count += 1
                if try_count == 4:
                    self.__sys_out("Failed to complete search", 2, True, True)
                    return False
            else:
                prev_progress = current_progress
                try_count = 0

            search_box = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.ID, "sb_form_q")))
            search_box.clear()

            # send query
            while True:
                if len(self.__queries) > 0:
                    query = self.__queries[0]
                    self.__queries = self.__queries[1:]
                else:
                    trending_date -= timedelta(days=1)
                    last_request_time = self.__update_search_queries(trending_date, last_request_time)
                    continue
                if query not in self.search_hist:
                    break

            search_box.send_keys(query, Keys.RETURN) # unique search term
            self.search_hist.append(query)
            time.sleep(random.uniform(2, 4.5))
            #originally used for location alerts
            #should no longer be an issue as geolocation is turned on
            try:
                driver.switch_to.alert.dismiss()
            except NoAlertPresentException:
                pass
        self.__sys_out("Successfully completed search", 2, True, True)
        return True

    def __get_quiz_progress(self, driver, try_count=0):
        try:
            #questions = driver.find_elements_by_xpath('//*[@id="rqHeaderCredits"]/div[2]/*')
            questions = driver.find_elements_by_xpath('//*[starts-with(@id, "rqQuestionState")]')
            if len(questions) > 0:
                current_progress, complete_progress = 0, len(questions)
                for question in questions:
                    if question.get_attribute("class") == "filledCircle":
                        current_progress += 1
                    else:
                        break
                return current_progress-1, complete_progress
            else:
                footer = driver.find_element_by_xpath('//*[@id="FooterText0"]').text
                current_progress = footer[0]
                complete_progress = footer[-1]
                return current_progress, complete_progress

        except:
            if try_count < 4:
                return self.__get_quiz_progress(driver, try_count+1)
            else:
                return 0, -1

    def __start_quiz(self, driver):
        try_count = 0
        while True:
            try:
                start_quiz = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.ID, 'rqStartQuiz')))
            #if quiz doesn't have a rStartQuiz element, it doesn't need to be prepped
            except TimeoutException:
                return True
            if start_quiz.is_displayed():
                try:
                    start_quiz.click()
                except:
                    driver.refresh()
                    time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
            else:
                try:
                    if driver.find_element_by_id("quizWelcomeContainer").get_attribute("style") == "display: none;": # started
                        self.__sys_out("Successfully started quiz", 3, True)
                        break
                except:
                    driver.refresh()
                    time.sleep(self.__WEB_DRIVER_WAIT_SHORT)

            try_count += 1
            if try_count == 3:
                self.__sys_out("Failed to start quiz", 3, True)
                return False
            time.sleep(3)

        return True

    def __multiple_answers(self, driver):
        '''
        A type of quiz with overlay that have multple questions (usually 3), and within each question, the user must select x amount of correct answers (usually 5). Examples of this type of question are warpspeed and supersonic quizzes
        '''
        while True:
            quiz_current_progress, quiz_complete_progress = self.__get_quiz_progress(driver)
            self.__sys_out_progress(quiz_current_progress, quiz_complete_progress, 4)
            #either on the last question, or just completed
            if quiz_current_progress == quiz_complete_progress - 1:
                try:
                    time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                    #quiz has been completed
                    if len(driver.find_elements_by_class_name('headerMessage')) > 0:
                        self.__sys_out_progress(quiz_complete_progress, quiz_complete_progress, 4)
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
                    if len(driver.find_elements_by_id('rqAnswerOption{0}'.format(option_index))) > 0:
                        #find_element_by_id returns an EventFiringWebElement object, to get the web element, must use wrapped_element attribute
                        element = driver.find_element_by_id('rqAnswerOption{0}'.format(option_index)).wrapped_element
                        #must use ActionChains due to error 'element is not clickable at point', for more info see this link:https://stackoverflow.com/questions/11908249/debugging-element-is-not-clickable-at-point-error
                        ActionChains(driver).move_to_element(element).click(element).perform()
                    else:
                        return False
                    time.sleep(random.uniform(1, 4))
                    prev_progress = question_progress
                    #returns a string like '1/5' (1 out of 5 answers selected correctly so far)
                    question_progress = driver.find_element_by_class_name('bt_corOpStat').text
                    #once the last correct answer is clicked, question progress becomes '' or 5/5, tho in the past it became '0/5' sometimes, hence 2nd cond
                    if (question_progress == '' or question_progress == '5/5') or (prev_progress != question_progress and question_progress in question_progresses):
                        #wait for the next question to appear
                        time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                        break
                    question_progresses.append(question_progress)
                    option_index += 1
            except:
                return False

    def __solve_tot(self, driver):
        '''
        Solves This or That quiz
        The answers are randomly selected, so on average, only half the points will be earned.
        '''
        while True:
            try_count = 0
            try:
                progress = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_element_located((By.CLASS_NAME, 'bt_Quefooter'))).text
                current_progress, complete_progress = map(int, progress.split(' of '))
                current_progress = current_progress - 1
                self.__sys_out_progress(current_progress, complete_progress, 4)
                driver.find_element_by_id('rqAnswerOption' + str(random.choice([0,1]))).click()
                time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                if current_progress == complete_progress - 1:
                    try:
                        header = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_element_located((By.CLASS_NAME, 'headerMessage')))
                        if "you earned" in header.text.lower():
                            self.__sys_out_progress(complete_progress, complete_progress, 4)
                            return True
                    #the header message could not be found
                    except:
                        return False
            except:
                try_count += 1
                if try_count >= 2:
                    self.__sys_out("Failed to complete This or That quiz", 3, True, True)
                    return False

    def __solve_hot_take(self, driver):
        try:
            driver.find_element_by_id('btoption{}'.format(random.choice(([0,1])))).click()
            return True
        except:
            self.__sys_out("Failed to complete Hot Takes", 3, True, True)
            return False

    def __quiz(self, driver):
        started = self.__start_quiz(driver)
        if not started:
            return started

        quiz_options_len = 4
        is_drag_and_drop = False
        is_tot = False
        is_hot_take = False
        is_multiple_answers = False

        if len(driver.find_elements_by_id('rqAnswerOptionNum0')) > 0:
            is_drag_and_drop = True
            self.__sys_out("Drag and drop", 3)
        elif len(driver.find_elements_by_class_name('btCorOps')) > 0:
            is_multiple_answers = True
            self.__sys_out("Multiple Answers", 3)
        elif len(driver.find_elements_by_class_name('btOptionAnsOvl')) > 0:
            is_tot = True
        elif len(driver.find_elements_by_id('btPollOverlay')) > 0:
            is_hot_take = True
        else:
            self.__sys_out("Multiple choice", 3)

        ## drag and drop
        if is_drag_and_drop:
            time.sleep(self.__WEB_DRIVER_WAIT_SHORT) # let demo complete

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
                current_progress, complete_progress = self.__get_quiz_progress(driver)
                if complete_progress > 0:
                    self.__sys_out_progress(current_progress, complete_progress, 4)

                # get all correct combinations so to not use them again
                correct_options = []
                option_index = 0
                while option_index < quiz_options_len:
                    try:
                        option = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_element_located((By.ID, "rqAnswerOption{0}".format(option_index))))
                        if option.get_attribute("class") == "rqOption rqDragOption correctAnswer":
                            correct_options.append(option_index)
                        option_index += 1
                    except TimeoutException:
                        self.__sys_out("Time out Exception", 3)
                        return False

                if current_progress != prev_progress: # new question
                    incorrect_options = []
                    prev_progress =  current_progress
                else:
                    # update incorrect options
                    incorrect_options.append((from_option_index, to_option_index))
                    incorrect_options.append((to_option_index, from_option_index))

                exit_code = -1 # no choices were swapped
                for combo in to_from_combos:
                    from_option_index, to_option_index = combo[0], combo[1]
                    # check if combination has already been tried
                    if combo not in incorrect_options and from_option_index not in correct_options and to_option_index not in correct_options:
                        # drag from option to to option
                        from_option = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_element_located((By.ID, "rqAnswerOption{0}".format(from_option_index))))
                        to_option = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_element_located((By.ID, "rqAnswerOption{0}".format(to_option_index))))
                        ActionChains(driver).drag_and_drop(from_option, to_option).perform()
                        time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                        #self.__handle_alerts(driver)

                        if current_progress == complete_progress-1: # last question
                            try:
                                #header = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="quizCompleteContainer"]/span/div[1]')))
                                header = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="quizCompleteContainer"]/div')))
                                #if header.text == "Way to go!":
                                if "great job" in header.text.lower():
                                    self.__sys_out_progress(complete_progress, complete_progress, 4)
                                    exit_code = 0 # successfully completed
                                    break
                            except:
                                pass
                        exit_code = 1 # successfully swapped 2 choices (can still be wrong)
                        break

                if exit_code == -1:
                    self.__sys_out("Failed to complete quiz1 - tried every choice", 3, True, True)
                    return False
                elif exit_code == 0:
                    break

        #multiple answers per question (i.e. warp speed/supersonic)
        elif is_multiple_answers:
            return self.__multiple_answers(driver)

        #this or that quiz
        elif is_tot:
            return self.__solve_tot(driver)

        elif is_hot_take:
            return self.__solve_hot_take(driver)

        ## multiple choice (i.e. lignting speed)
        else:
            prev_progress = -1
            prev_options = []
            try_count = 0
            prev_complete_progress = 0 # complete progress becomes 0 at end of quiz, for printing purposes
            while True:
                current_progress, complete_progress = self.__get_quiz_progress(driver)
                if complete_progress > 0:
                    #selected the correct answer
                    if current_progress != prev_progress:
                        self.__sys_out_progress(current_progress, complete_progress, 4)
                        prev_progress = current_progress
                        prev_options = []
                        try_count = 0
                        prev_complete_progress = complete_progress
                else:
                    try_count += 1
                    if try_count == quiz_options_len:
                        self.__sys_out("Failed to complete quiz1 - no progress", 3, True, True)
                        return False

                if current_progress == complete_progress-1: # last question, works for -1, 0 too (already complete)
                    try:
                        #header = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="quizCompleteContainer"]/span/div[1]')))
                        header = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="quizCompleteContainer"]/div')))
                        #if header.text == "Way to go!":
                        if "great job" in header.text.lower():
                            if prev_complete_progress > 0:
                                self.__sys_out_progress(prev_complete_progress, prev_complete_progress, 4)
                                break
                            else:
                                self.__sys_out("Already completed quiz", 3, True)
                                return True
                    except:
                        pass

                # select choice
                for option_index in range(quiz_options_len):
                    if option_index not in prev_options:
                        break
                if option_index in prev_options:
                    self.__sys_out("Failed to complete quiz1 - tried every choice", 3, True, True)
                    return False

                try:
                    # click choice
                    WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.element_to_be_clickable((By.ID, "rqAnswerOption{0}".format(option_index)))).click()
                    prev_options.append(option_index)
                    time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                    #self.__handle_alerts(driver)
                except TimeoutException:
                    self.__sys_out("Time out Exception", 3)
                    return False

        self.__sys_out("Successfully completed quiz", 3, True, True)
        return True

    def __quiz2(self, driver):
        self.__sys_out("Starting quiz2 (no overlay)", 3)
        current_progress, complete_progress = 0, -1

        while current_progress != complete_progress:
            try:
                progress = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="QuestionPane{}"]/div[2]'.format(current_progress)))).text
            except TimeoutException:
                self.__sys_out("Could not find quiz2 progress elements", 3)
                return False
            current_progress, complete_progress = [int(x) for x in re.match("\((\d+) of (\d+)\)", progress).groups()]
            self.__sys_out_progress(current_progress-1, complete_progress, 4)
            time.sleep(random.uniform(1, 3))
            driver.find_elements_by_class_name('wk_Circle')[random.randint(0,2)].click()
            time.sleep(self.__WEB_DRIVER_WAIT_SHORT)

            is_clicked, try_count = False, 0
            #sometimes the 'next' button isn't clickable and page needs to be refreshed
            while not is_clicked:
                if len(driver.find_elements_by_class_name('cbtn')) > 0:
                    WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cbtn'))).click()
                elif len(driver.find_elements_by_class_name('wk_button')) > 0:
                    WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.element_to_be_clickable((By.CLASS_NAME, 'wk_button'))).click()
                elif len(driver.find_elements_by_id('check')) > 0:
                    WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.element_to_be_clickable((By.ID, 'check'))).click()
                else:
                    self.__sys_out("Failed to complete quiz2", 3, True, True)
                    return False

                try:
                    if current_progress != complete_progress:
                        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="QuestionPane{}"]/div[2]'.format(current_progress)))).text
                    is_clicked = True

                except:
                    #implies one of the next buttons was found, but wasn't able to click it
                    driver.refresh()
                    try_count += 1
                    if try_count == 2:
                        self.__sys_out("Quiz2 element not clickable", 3, True, True)
                        return False

        #if current_progress == complete_progress:
        self.__sys_out_progress(current_progress, complete_progress, 4)
        self.__sys_out("Successfully completed quiz2", 3, True, True)
        return True

    def __poll(self, driver, title):
        self.__sys_out("Starting poll", 3)
        time.sleep(self.__WEB_DRIVER_WAIT_SHORT)

        #for daily poll
        if 'daily' in title:
            element_id = 'btoption{0}'.format(random.randint(0,1))
        #all other polls
        else:
            #xpath = '//*[@id="OptionText0{}"]'.format(random.randint(0, 1))
            element_id = 'OptionText0{0}'.format(random.randint(0,1))

        try:
            WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.element_to_be_clickable((By.ID, element_id))).click()
            self.__sys_out("Successfully completed poll", 3, True)
            return True
        except:
            self.__sys_out("Failed to complete poll", 3, True)
            return False

    def __handle_alerts(self, driver):
        try:
            driver.switch_to.alert.dismiss()
        except:
            pass

    def __is_offer_sign_in_bug(self, driver):
        '''
        Sometimes when clicking an offer for the first time, it will show a page saying the user is not signed in. Pretty sure it's a Bing bug. This method checks for this bug
        '''
        try:
            driver.find_element_by_class_name('identityStatus')
            return True
        except:
            return False

    def __has_overlay(self, driver):
        '''most offers that have the word 'quiz' in title have a btOverlay ID. However, certain quizzes that related to special events i.e. halloween do not have this overlay'''
        self.__sys_out("Starting quiz", 3)
        try_count = 0
        while True:
            try:
                driver.find_element_by_id("btOverlay")
                return True
            except:
                try_count += 1
                if try_count >= 1:
                    self.__sys_out("Could not detect quiz overlay", 3, True)
                    return False
                time.sleep(2)

    def __click_offer(self, driver, offer, title_xpath, checked_xpath, details_xpath, link_xpath):
        title = offer.find_element_by_xpath(title_xpath).text
        self.__sys_out("Trying {0}".format(title), 2)

        # check whether it was already completed
        checked = False
        try:
            icon = offer.find_element_by_xpath(checked_xpath)
            if icon.get_attribute('class').startswith("mee-icon mee-icon-SkypeCircleCheck"):
                checked = True
                self.__sys_out("Already checked", 2, True)
        #quiz does not contain a check-mark icon, implying no points offered
        except:
            checked = True
            self.__sys_out("skipping quiz - assuming it offers no points", 3)

        completed = True
        if not checked:
            details = offer.find_element_by_xpath(details_xpath).text

            offer.find_element_by_xpath(link_xpath).click()
            #driver.execute_script('''window.open("{0}","_blank");'''.format(offer.get_attribute("href")))
            driver.switch_to.window(driver.window_handles[-1])
            #self.__handle_alerts(driver)
            
            #Check for cookies popup
            self.__sys_out("Checking cookies popup", 3)
            time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
            try:
                WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.element_to_be_clickable((By.ID, "bnp_btn_accept"))).click()
                time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                self.__sys_out("cookie popup cleared", 3)
            except:
                self.__sys_out("No cookie popup present", 3)
            if self.__is_offer_sign_in_bug(driver):
                completed = -1

            elif "poll" in title.lower():
                completed = self.__poll(driver, title.lower())

            #if "quiz" in title.lower()
            else:
                if self.__has_overlay(driver):
                    completed = self.__quiz(driver)
                else:
                    completed = self.__quiz2(driver)

            if completed == -1:
                self.__sys_out("Sign in Bing bug for offer {0}, will try again".format(title), 2, True)
            elif completed:
                self.__sys_out("Successfully completed {0}".format(title), 2, True)
            else:
                self.__sys_out("Failed to complete {0}".format(title), 2, True)

            driver.switch_to.window(driver.window_handles[0])
            driver.get(self.__DASHBOARD_URL) # for stale element exception

        return completed

    def map_offers(self, driver):
        '''
        Creates a dictionary where (k, v)= (offer title, offer element)
        Useful for testing individual offers
        '''
        driver.get(self.__DASHBOARD_URL)
        title_to_offer = {}
        for i in range(3):
            offer = driver.find_element_by_xpath('//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{}]/div/card-content/mee-rewards-daily-set-item-content/div'.format(i+1))
            title = offer.find_element_by_xpath('./div[2]/h3').text
            title_to_offer[title] = offer

        for i in range(30):
            try:
                offer = driver.find_element_by_xpath('//*[@id="more-activities"]/div/mee-card[{}]/div/card-content/mee-rewards-more-activities-card-item/div'.format(i+1))
                title = offer.find_element_by_xpath('./div[2]/h3').text
                title_to_offer[title] = offer
                i += 1
            except:
                pass
        return title_to_offer

    def __offers(self, driver):
        ## showcase offer
        driver.get(self.__DASHBOARD_URL)
        completed = []
        #try statement in case we try to find an offer that exceeded the range index
        try:
            #daily set
            for i in range(3):
                #c will remain -1 if sign in bug page is reached
                c = -1
                #try the page again if sign in bug
                try_count = 0
                while c == -1 and try_count <= 2:
                    offer = driver.find_element_by_xpath('//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{}]/div/card-content/mee-rewards-daily-set-item-content/div'.format(i+1))
                    c = self.__click_offer(driver, offer, './div[2]/h3', './mee-rewards-points/div/div/span[1]', './div[2]/p', './div[3]/a/span/ng-transclude')
                    try_count += 1
                #first quiz never started (MS bug) but pts still awarded
                if i == 0:
                    completed.append(True)
                else:
                    completed.append(c)
        except NoSuchElementException:
            completed.append(-1)

        try:
            #remaining_offers = driver.find_elements_by_xpath('//*[starts-with(@id, "more-activities"])')#/div/mee-card)')
            remaining_offers = driver.find_elements_by_xpath('//*[@id="more-activities"]/div/mee-card')
            for i in range(len(remaining_offers)):
                c = -1
                try_count = 0
                while c == -1 and try_count <= 2:
                    offer = driver.find_element_by_xpath('//*[@id="more-activities"]/div/mee-card[{}]/div/card-content/mee-rewards-more-activities-card-item/div'.format(i+1))
                    c = self.__click_offer(driver, offer, './div[2]/h3', './mee-rewards-points/div/div/span[1]', './div[2]/p', './div[3]/a/span/ng-transclude')
                    try_count += 1
                completed.append(c)

        except NoSuchElementException:
            print( NoSuchElementException)
            completed.append(-1)
        return min(completed)

    def __complete_edge_search(self, driver=None, close=False):
        self.__sys_out("Starting Edge search", 1)

        try:
            if driver is None:
                driver = Driver.get_driver(self.path, Driver.WEB_DEVICE, self.headless)
                self.__login(driver)
            self.completion.edge_search = self.__search(driver, Driver.WEB_DEVICE, is_edge=True)
            if self.completion.edge_search:
                self.__sys_out("Successfully completed edge search", 1, True)
            else:
                self.__sys_out("Failed to complete edge search", 1, True)
        except:
            try:
                driver.quit()
            except: # not yet initialized
                pass
            raise

        if close:
            driver.quit()
        else:
            return driver

    def __complete_web_search(self, driver=None, close=False):
        self.__sys_out("Starting web search", 1)

        try:
            if driver is None:
                driver = Driver.get_driver(self.path, Driver.WEB_DEVICE, self.headless)
                self.__login(driver)
            self.completion.web_search = self.__search(driver, Driver.WEB_DEVICE)
            if self.completion.web_search:
                self.__sys_out("Successfully completed web search", 1, True)
            else:
                self.__sys_out("Failed to complete web search", 1, True)
        except:
            try:
                driver.quit()
            except: # not yet initialized
                pass
            raise

        if close:
            driver.quit()
        else:
            return driver

    def __complete_mobile_search(self, driver=None, close=False):
        self.__sys_out("Starting mobile search", 1)

        try:
            if driver is None:
                driver = Driver.get_driver(self.path, Driver.MOBILE_DEVICE, self.headless)
                self.__login(driver)

            self.completion.mobile_search = self.__search(driver, Driver.MOBILE_DEVICE)
            if self.completion.mobile_search:
                self.__sys_out("Successfully completed mobile search", 1, True)
            else:
                self.__sys_out("Failed to complete mobile search", 1, True)
        except:
            try:
                driver.quit()
            except: # not yet initialized
                pass
            raise

        if close:
            driver.quit()
        else:
            return driver
    def __complete_offers(self, driver=None):
        self.__sys_out("Starting offers", 1)

        try:
            if not driver:
                driver = Driver.get_driver(self.path, Driver.WEB_DEVICE, self.headless)
                self.__login(driver)

            self.completion.offers = self.__offers(driver)
            if self.completion.offers == -1 or self.completion.offers == False:
                self.__sys_out("Failed to complete offers", 1, True)
            else:
                self.__sys_out("Successfully completed offers", 1, True)
        except:
            try:
                driver.quit()
            except:
                pass
            raise

        return driver

    def __print_stats(self, driver):
        try:
            driver.get(self.__DASHBOARD_URL)
            #once pointsbreakdown link is clickable, page is loaded
            WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="rx-user-status-action"]/span/ng-transclude')))
            #sleep an additional 5 seconds to make sure stats are loaded
            time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
            stats = driver.find_elements_by_xpath('//mee-rewards-counter-animation//span')

            earned_index = 4
            streak_index = 2
            days_till_bonus_index = 3
            avail_index = 0

            if len(stats) == 6:
                IS_LEVEL_TWO = False
            elif len(stats) == 5:
                IS_LEVEL_TWO = True

            if IS_LEVEL_TWO:
                self.__sys_out("Summary", 1, flush=True)
                self.__sys_out("Points earned: " + stats[earned_index].text.replace(" ", ""), 2)
                self.__sys_out("Streak count: " + stats[streak_index].text, 2)
                self.__sys_out(stats[days_till_bonus_index].text, 2, end=True) # streak details, ex. how many days remaining, bonus earned
                self.__sys_out("Available points: " + stats[avail_index].text, 2)

            else:
                self.__sys_out("Summary", 1, flush=True)
                self.__sys_out("Points earned: " + stats[earned_index+1].text.replace(" ", ""), 2)
                self.__sys_out("Streak count: " + stats[streak_index+1].text, 2)
                self.__sys_out(stats[days_till_bonus_index+1].text, 2, end=True) # streak details, ex. how many days remaining, bonus earned
                self.__sys_out("Available points: " + stats[avail_index+1].text, 2)

        except Exception as e:
            print('    Error checking rewards status - ', e)

    def print_stats(self, driver, is_print_stats):
        self.__print_stats(driver)
        driver.quit()
    def complete_edge_search(self, search_hist, is_print_stats=True):
        self.search_hist = search_hist
        driver = self.__complete_edge_search()
        if is_print_stats:
            self.print_stats(driver, is_print_stats)
    def complete_web_search(self, search_hist, is_print_stats=True):
        self.search_hist = search_hist
        driver = self.__complete_web_search()
        if is_print_stats:
            self.print_stats(driver, is_print_stats)
    def complete_mobile_search(self, search_hist, is_print_stats=True):
        self.search_hist = search_hist
        driver = self.__complete_mobile_search()
        if is_print_stats:
            self.print_stats(driver, is_print_stats)
    def complete_offers(self, is_print_stats=True):
        driver = self.__complete_offers()
        if is_print_stats:
            self.print_stats(driver, is_print_stats)
    def complete_both_searches(self, search_hist, is_print_stats=True):
        self.search_hist = search_hist
        driver = self.__complete_edge_search()
        self.__complete_web_search(driver, close=True)
        driver = self.__complete_mobile_search()
        if is_print_stats:
            self.print_stats(driver, is_print_stats)
    def complete_all(self, search_hist, is_print_stats=True):
        self.search_hist = search_hist
        driver = self.__complete_edge_search()
        self.__complete_web_search(driver)
        self.__complete_offers(driver)
        driver.quit()
        driver = self.__complete_mobile_search()
        if is_print_stats:
            self.print_stats(driver, is_print_stats)
