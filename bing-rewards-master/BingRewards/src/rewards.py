from src.driver import Driver
from src.log import Completion
from urllib.request import urlopen
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
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
    __DASHBOARD_URL             = "https://account.microsoft.com/rewards/dashboard"
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
            WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_element_located((By.ID, "i0118"))).send_keys(base64.b64decode(self.password).decode(), Keys.RETURN)
        except:
            ActionChains(driver).send_keys(base64.b64decode(self.password).decode(), Keys.RETURN).perform()

        self.__sys_out("Successfully logged in", 2, True)

    def __get_search_progress(self, driver, device):
        if len(driver.window_handles) == 1: # open new tab
            driver.execute_script('''window.open("{0}");'''.format(self.__POINTS_URL))
        driver.switch_to.window(driver.window_handles[-1])
        
        driver.refresh()
        progress_elements = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_all_elements_located((By.XPATH, '//*[@id="userPointsBreakdown"]/div/div[*]')))[1:]

        if device == Driver.WEB_DEVICE:
            web_progress_elements = [None, None]
            for element in progress_elements:
                progress_name = element.find_element_by_xpath('./div/div[2]/mee-rewards-user-points-details/div/div/div/div/p[1]').text.lower()
                if "pc" in progress_name or ("daily" in progress_name and "activities" not in progress_name):
                    web_progress_elements[0] = element.find_element_by_xpath('./div/div[2]/mee-rewards-user-points-details/div/div/div/div/p[2]')
                elif "bonus" in progress_name:
                    web_progress_elements[1] = element.find_element_by_xpath('./div/div[2]/mee-rewards-user-points-details/div/div/div/div/p[2]')

            if web_progress_elements[0]:
                current_progress, complete_progress = [int(i) for i in re.findall(r'(\d+)', web_progress_elements[0].text)]

                # get bonus points 
                if web_progress_elements[1]:
                    bonus_progress = [int(i) for i in re.findall(r'(\d+)', web_progress_elements[1].text)]
                    current_progress += bonus_progress[0]
                    complete_progress += bonus_progress[1]

            else:
                current_progress, complete_progress = 0, -1

        else:
            mobile_progress_element = None
            for element in progress_elements:
                progress_name = element.find_element_by_xpath('./div/div[2]/mee-rewards-user-points-details/div/div/div/div/p[1]').text.lower()
                if "mobile" in progress_name or ("daily" in progress_name and "activities" not in progress_name):
                    mobile_progress_element = element.find_element_by_xpath('./div/div[2]/mee-rewards-user-points-details/div/div/div/div/p[2]')

            if mobile_progress_element:
                current_progress, complete_progress = [int(i) for i in re.findall(r'(\d+)', mobile_progress_element.text)]

            else:
                current_progress, complete_progress = 0, -1

        driver.switch_to.window(driver.window_handles[0])
        #driver.get(self.__BING_URL)
        return current_progress, complete_progress
    def __update_search_queries(self, timestamp, last_request_time):
        if last_request_time:
            time.sleep(max(0, 20-(datetime.now()-last_request_time).total_seconds())) # sleep at least 20 seconds to avoid over requesting server
        response = urlopen(self.__TRENDS_URL.format(timestamp.strftime("%Y%m%d")), context=ssl.SSLContext(ssl.PROTOCOL_TLSv1))
        last_request_time = datetime.now()
        response = json.loads(response.read()[5:])

        #self.__queries = [] # will already be empty
        for topic in response["default"]["trendingSearchesDays"][0]["trendingSearches"]:
            self.__queries.append(topic["title"]["query"].lower())
            for related_topic in topic["relatedQueries"]:
                self.__queries.append(related_topic["query"].lower())
        return last_request_time
    def __search(self, driver, device):
        self.__sys_out("Starting search", 2)
        driver.get(self.__BING_URL)    

        prev_progress = -1
        try_count = 0
        trending_date = datetime.now()

        last_request_time = None
        if len(self.__queries) == 0:
            last_request_time = self.__update_search_queries(trending_date, last_request_time)
        while True:
            current_progress, complete_progress = self.__get_search_progress(driver, device)
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
        
            search_box = driver.find_element_by_id("sb_form_q")
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


            # sleep for a few seconds
            time.sleep(random.uniform(0, 5))

        self.__sys_out("Successfully completed search", 2, True, True)
        return True

    def __get_quiz_progress(self, driver, try_count=0):
        try:
            #questions = driver.find_elements_by_xpath('//*[@id="rqHeaderCredits"]/div[2]/*')
            questions = driver.find_elements_by_xpath('//*[starts-with(@id, "rqQuestionState")]')
            current_progress, complete_progress = 0, len(questions)
            for question in questions:
                if question.get_attribute("class") == "filledCircle":
                    current_progress += 1
                else:
                    break
            return current_progress-1, complete_progress
        except:
            if try_count < 4:
                return self.__get_quiz_progress(driver, try_count+1)
            else:
                return 0, -1
    def __start_quiz(self, driver):
        try_count = 0
        while True:
            try:
                driver.find_element_by_id("btOverlay")
                break
            except:
                try_count += 1
                if try_count == 4:
                    self.__sys_out("Failed to start quiz - could not detect quiz overlay", 3, True)
                    return False
                time.sleep(1)

        try:
            try_count = 0
            while True:
                start_quiz = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.ID, 'rqStartQuiz')))
                if start_quiz.is_displayed():
                    try:
                        start_quiz.click()
                    except:
                        driver.refresh()
                else:
                    try:
                        if driver.find_element_by_id("quizWelcomeContainer").get_attribute("style") == "display: none;": # started
                            self.__sys_out("Successfully started quiz", 3, True)
                            break
                    except: 
                        driver.refresh()

                try_count += 1
                if try_count == 4:
                    self.__sys_out("Failed to start quiz", 3, True)
                    return False
                time.sleep(1)
        except:
            self.__sys_out("Already started quiz", 3, True)

        return True
    def __quiz(self, driver):
        self.__sys_out("Starting quiz", 3)

        started = self.__start_quiz(driver)
        if not started:
            return started


        quiz_options_len = 4

        is_drag_and_drop = False
        try:
            WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.ID, 'rqAnswerOptionNum0')))
            is_drag_and_drop = True
            self.__sys_out("Drag and drop", 3)
        except:
            self.__sys_out("Multiple choice", 3)


        ## drag and drop
        if is_drag_and_drop:
            time.sleep(5) # let demo complete

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
                    option = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_element_located((By.ID, "rqAnswerOption{0}".format(option_index))))
                    #if option.get_attribute("class") == "rqOption rqDragOption correctDragAnswer":
                    if option.get_attribute("class") == "rqOption rqDragOption correctAnswer":
                        correct_options.append(option_index)
                    option_index += 1

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
                                if "great job!" in header.text.lower():
                                    self.__sys_out_progress(complete_progress, complete_progress, 4)
                                    exit_code = 0 # successfully completed
                                    break
                            except:
                                pass
                        exit_code = 1 # successfully swapped 2 choices (can still be wrong)
                        break
                
                if exit_code == -1: 
                    self.__sys_out("Failed to complete quiz - tried every choice", 3, True, True)
                    return False
                elif exit_code == 0:
                    break



        ## multiple choice
        else:
            prev_progress = -1
            prev_options = []
            try_count = 0
            prev_complete_progress = 0 # complete progress becomes 0 at end of quiz, for printing purposes
            while True:
                current_progress, complete_progress = self.__get_quiz_progress(driver)
                if complete_progress > 0:
                    if current_progress != prev_progress:
                        self.__sys_out_progress(current_progress, complete_progress, 4)
                        prev_progress = current_progress
                        prev_options = []
                        try_count = 0
                        prev_complete_progress = complete_progress
                else:
                    try_count += 1
                    if try_count == quiz_options_len:
                        self.__sys_out("Failed to complete quiz - no progress", 3, True, True)
                        return False

                if current_progress == complete_progress-1: # last question, works for -1, 0 too (already complete)
                    try:
                        #header = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="quizCompleteContainer"]/span/div[1]')))
                        header = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_SHORT).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="quizCompleteContainer"]/div')))
                        #if header.text == "Way to go!":
                        if "great job!" in header.text.lower():
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
                    self.__sys_out("Failed to complete quiz - tried every choice", 3, True, True)
                    return False

                # click choice
                WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.element_to_be_clickable((By.ID, "rqAnswerOption{0}".format(option_index)))).click()
                prev_options.append(option_index)
                time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
                #self.__handle_alerts(driver)


        self.__sys_out("Successfully completed quiz", 3, True, True)
        return True

    def __quiz2(self, driver):
        self.__sys_out("Starting weekly quiz (new)", 3)
        time.sleep(self.__WEB_DRIVER_WAIT_SHORT)

        current_progress = 0
        while True:
            try:
                progress = WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.visibility_of_element_located((By.ID, "FooterText{}".format(current_progress)))).text
                current_progress, complete_progress = [int(x) for x in re.match("\((\d+) of (\d+)\)", progress).groups()]
                self.__sys_out_progress(current_progress-1, complete_progress, 4)

                driver.find_element_by_xpath('//*[@id="QuestionPane{}"]/div[1]/div[2]/div[1]'.format(current_progress-1)).click() # correct answer not required
                WebDriverWait(driver, self.__WEB_DRIVER_WAIT_LONG).until(EC.element_to_be_clickable((By.ID, "check"))).click()

                if current_progress == complete_progress:
                    self.__sys_out_progress(current_progress, complete_progress, 4)
                    break
            except:
                self.__sys_out("Failed to complete quiz", 3, True, True)
                return False

        self.__sys_out("Successfully completed quiz", 3, True, True)
        return True
    def __poll(self, driver):
        self.__sys_out("Starting poll", 3)
        time.sleep(self.__WEB_DRIVER_WAIT_SHORT)

        try:
            driver.find_element_by_xpath('//*[@id="OptionText0{}"]'.format(random.randint(0, 1))).click() # first option
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
    def __click_offer(self, driver, offer, title_xpath, checked_xpath, details_xpath, link_xpath):
        title = offer.find_element_by_xpath(title_xpath).text
        self.__sys_out("Trying {0}".format(title), 2)

        # check whether it was already completed
        checked = False
        try:
            icon = offer.find_element_by_xpath(checked_xpath)
            if icon.get_attribute('class').startswith("mee-icon mee-icon-SkypeCircleCheck ng-scope"):
                checked = True
                self.__sys_out("Already checked", 2, True)
        except:
            self.__sys_out("Assuming not already checked", 3)

        completed = True
        if not checked:
            details = offer.find_element_by_xpath(details_xpath).text

            offer.find_element_by_xpath(link_xpath).click()
            #driver.execute_script('''window.open("{0}","_blank");'''.format(offer.get_attribute("href")))
            driver.switch_to.window(driver.window_handles[-1])
            #self.__handle_alerts(driver)

            if "quiz" in title.lower():
                completed = self.__quiz(driver)
            #elif "quiz" in details.lower():
            elif title.lower() == "test your smarts":
                completed = self.__quiz2(driver)
            elif "poll" in title.lower():
                completed = self.__poll(driver)
            else:
                time.sleep(self.__WEB_DRIVER_WAIT_SHORT)
            if completed:
                self.__sys_out("Successfully completed {0}".format(title), 2, True)
            else:
                self.__sys_out("Failed to complete {0}".format(title), 2, True)

            driver.switch_to.window(driver.window_handles[0])
            driver.get(self.__DASHBOARD_URL) # for stale element exception
        
        return completed
    def __offers(self, driver):
        ## showcase offer
        driver.get(self.__DASHBOARD_URL)
        
        completed = []
        ## daily set
        for i in range(3):
            #offer = driver.find_element_by_xpath('//*[@id="daily-sets"]/mee-rewards-card-placement[1]/div/div/div[{}]/{}/mee-rewards-daily-sets-item/mee-rewards-card/div/div'.format(1 if i == 0 else 2, 'item{}'.format(i) if i == 0 else 'div[{0}]/item{0}'.format(i)))
            #c = self.__click_offer(driver, offer, './section/div/div[2]/h3', './section/div/div[2]/mee-rewards-points/div/div/span[1]', './section/div/div[2]/p')
            offer = driver.find_element_by_xpath('//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{}]/div/card-content/mee-rewards-daily-set-item-content/div'.format(i+1))
            c = self.__click_offer(driver, offer, './div[2]/h3', './mee-rewards-points/div/div/span[1]', './div[2]/p', './div[3]')
            completed.append(c)

        ### more activities
        #item_num = 0
        #i = 0
        #while i < 8:
        #    # if offer takes up 2 spaces length wise
        #    try:
        #        offer = driver.find_element_by_xpath('//*[@id="more-activities"]/div/div/div[{}]/item{}/mee-rewards-more-activities-item/mee-mosaic-item/div/section/div'.format(int(i/2)+1, item_num))
        #        c = self.__click_offer(driver, offer, './div[2]/h3', './mee-rewards-points/div/div/span[1]', './div[2]/p')
        #        completed.append(c)
        #        i += 1
        #        item_num += 1
        #    except:
        #        # if offer takes up 1 space
        #        try:
        #            offer = driver.find_element_by_xpath('//*[@id="more-activities"]/div/div/div[{}]/div[{}]/item{}/mee-rewards-more-activities-item/mee-mosaic-item/div/section/div'.format(int(i/2)+1, (i%2)+1, item_num))
        #            c = self.__click_offer(driver, offer, './div[2]/h3', './mee-rewards-points/div/div/span[1]', './div[2]/p')
        #            completed.append(c)
        #            item_num += 1
        #        # if offer takes up 4 spaces (length 2, width 2)
        #        except:
        #            pass
        #    i += 1

        # '//*[@id="punch-cards"]/mee-hero-item/section/div/div/div'

        for i in range(8):
            try:
                offer = driver.find_element_by_xpath('//*[@id="more-activities"]/div/mee-card[{}]/div/card-content/mee-rewards-more-activities-card-item/div'.format(i+1))
                c = self.__click_offer(driver, offer, './div[2]/h3', './mee-rewards-points/div/div/span[1]', './div[2]/p', './div[3]')
                completed.append(c)
                i += 1
                item_num += 1
            except:
                pass

        return min(completed)


    def __complete_web_search(self, close=False):
        self.__sys_out("Starting web search", 1)

        try:
            driver = Driver.get_driver(self.path, Driver.WEB_DEVICE, self.headless)
            self.__login(driver)
        
            self.completion.web_search = self.__search(driver, Driver.WEB_DEVICE)
            if self.completion.web_search:
                self.__sys_out("Successfully completed web search", 1, True)
            else:
                self.__sys_out("Failed to complete web search", 1, True)
        except:
            try:
                Driver.close(driver)
            except: # not yet initialized
                pass
            raise

        if close:
            Driver.close(driver)
        else:
            return driver
    def __complete_mobile_search(self, close=False): 
        self.__sys_out("Starting mobile search", 1)

        try:
            driver = Driver.get_driver(self.path, Driver.MOBILE_DEVICE, self.headless)
            self.__login(driver)
    
            self.completion.mobile_search = self.__search(driver, Driver.MOBILE_DEVICE)
            if self.completion.mobile_search:
                self.__sys_out("Successfully completed mobile search", 1, True)
            else:
                self.__sys_out("Failed to complete mobile search", 1, True)
        except:
            try:
                Driver.close(driver)
            except: # not yet initialized
                pass
            raise

        if close:
            Driver.close(driver)
        else:
            return driver
    def __complete_offers(self, driver=None):
        self.__sys_out("Starting offers", 1)

        try:
            if not driver:
                driver = Driver.get_driver(self.path, Driver.WEB_DEVICE, self.headless)
                self.__login(driver)
        
            self.completion.offers = self.__offers(driver)
            if self.completion.offers:
                self.__sys_out("Successfully completed offers", 1, True)
            else:
                self.__sys_out("Failed to complete offers", 1, True)
        except:
            try:
                Driver.close(driver)
            except:
                pass
            raise

        return driver
    def __print_stats(self, driver): 
        try: 
            driver.get(self.__DASHBOARD_URL)
            time.sleep(self.__WEB_DRIVER_WAIT_LONG)
            stats = driver.find_elements_by_id('$ctrl.id')

            self.__sys_out("Summary", 1, flush=True)
            self.__sys_out("Points earned: "+stats[4].text.replace(" ", ""), 2)
            self.__sys_out("Streak count: "+stats[2].text, 2)
            self.__sys_out(stats[3].text, 2, end=True) # streak details, ex. how many days remaining, bonus earned
            self.__sys_out("Available points: "+stats[0].text, 2)
        except Exception as e: 
            print('    Error checking rewards status - ', e)

    def complete_mobile_search(self, search_hist, print_stats=True): 
        self.search_hist = search_hist
        driver = self.__complete_mobile_search()
        if print_stats:
            self.__print_stats(driver)
        Driver.close(driver)
    def complete_web_search(self, search_hist, print_stats=True):
        self.search_hist = search_hist
        driver = self.__complete_web_search()
        if print_stats:
            self.__print_stats(driver)
        Driver.close(driver)
    def complete_both_searches(self, search_hist, print_stats=True):
        self.search_hist = search_hist
        self.__complete_web_search(close=True)
        driver = self.__complete_mobile_search()
        if print_stats:
            self.__print_stats(driver)
        Driver.close(driver)
    def complete_offers(self, print_stats=True):
        driver = self.__complete_offers()
        if print_stats:
            self.__print_stats(driver)
        Driver.close(driver)
    def complete_all(self, search_hist, print_stats=True):
        self.search_hist = search_hist
        driver = self.__complete_web_search()
        self.__complete_offers(driver)
        Driver.close(driver)
        driver = self.__complete_mobile_search()
        if print_stats:
            self.__print_stats(driver)
        Driver.close(driver)
    def complete_web_search_and_offers(self, search_hist, print_stats=True):
        self.search_hist = search_hist
        driver = self.__complete_web_search()
        self.__complete_offers(driver)
        if print_stats:
            self.__print_stats(driver)
        Driver.close(driver)

