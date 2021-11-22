import os
import platform
from urllib.request import urlopen
import ssl
import zipfile
from selenium import webdriver
from selenium.webdriver.support.abstract_event_listener import AbstractEventListener
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebDriver
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
import re


class EventListener(AbstractEventListener):
    """Attempt to disable animations"""
    def after_click_on(self, url, driver):
        animation =\
        """
        try { jQuery.fx.off = true; } catch(e) {}
        """
        driver.execute_script(animation)


class Driver:
    WEB_DEVICE = 0
    MOBILE_DEVICE = 1

    # Microsoft Edge user agents for additional points
    #agent src: https://www.whatismybrowser.com/guides/the-latest-user-agent/edge
    __WEB_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/94.0.992.50"
    __MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 10; HD1913) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.50 Mobile Safari/537.36 EdgA/93.0.961.53"

    def __download_driver(driver_path, system, dl_try_count=0):
        # determine latest chromedriver version
        #version selection faq: http://chromedriver.chromium.org/downloads/version-selection
        CHROME_RELEASE_URL = "https://sites.google.com/chromium.org/driver/downloads?authuser=0"
        try:
            response = urlopen(
                CHROME_RELEASE_URL,
                context=ssl.SSLContext(ssl.PROTOCOL_TLS)
            ).read()
        except ssl.SSLError:
            response = urlopen(
                CHROME_RELEASE_URL
            ).read()
        #download second latest version,most recent is sometimes not out to public yet

        latest_version = re.findall(
            b"ChromeDriver \d{2,3}\.0\.\d{4}\.\d+", response
        )[dl_try_count].decode().split()[1]
        print('Downloading chromedriver version: ' + latest_version)

        if system == "Windows":
            url = "https://chromedriver.storage.googleapis.com/{}/chromedriver_win32.zip".format(
                latest_version
            )
        elif system == "Darwin":
            url = "https://chromedriver.storage.googleapis.com/{}/chromedriver_mac64.zip".format(
                latest_version
            )
        elif system == "Linux":
            url = "https://chromedriver.storage.googleapis.com/{}/chromedriver_linux64.zip".format(
                latest_version
            )

        try:
            response = urlopen(
                url, context=ssl.SSLContext(ssl.PROTOCOL_TLS)
            )  # context args for mac
        except ssl.SSLError:
            response = urlopen(url)  # context args for mac
        zip_file_path = os.path.join(
            os.path.dirname(driver_path), os.path.basename(url)
        )
        with open(zip_file_path, 'wb') as zip_file:
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break
                zip_file.write(chunk)

        extracted_dir = os.path.splitext(zip_file_path)[0]
        with zipfile.ZipFile(zip_file_path, "r") as zip_file:
            zip_file.extractall(extracted_dir)
        os.remove(zip_file_path)

        driver = os.listdir(extracted_dir)[0]
        try:
            os.rename(os.path.join(extracted_dir, driver), driver_path)
        #for Windows
        except FileExistsError:
            os.replace(os.path.join(extracted_dir, driver), driver_path)

        os.rmdir(extracted_dir)
        os.chmod(driver_path, 0o755)

    def add_chrome_options(device, headless, cookies):
        options = webdriver.ChromeOptions()

        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1280,1024")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-notifications")
        options.add_argument("disable-infobars")

        options.add_experimental_option(
            "prefs", {
                # geolocation permission, 0=Ask, 1=Allow, 2=Deny
                "profile.default_content_setting_values.geolocation": 1,
                "profile.default_content_setting_values.notifications": 2
            }
        )

        if headless:
            options.add_argument("--headless")

        if device == Driver.WEB_DEVICE:
            options.add_argument("user-agent=" + Driver.__WEB_USER_AGENT)
        else:
            options.add_argument("user-agent=" + Driver.__MOBILE_USER_AGENT)

        if cookies:
            options.add_argument("user-data-dir=stored_browser_data")
            #option 1
            #options.add_argument('--remote-debugging-port=9222')
            #option 2
            #options.add_argument('--no-sandbox')
            #options.add_argument('--disable-dev-shm-usage')
        return options

    def get_driver(path, device, headless, cookies):
        system = platform.system()
        if system == "Windows":
            if not path.endswith(".exe"):
                path += ".exe"
        if not os.path.exists(path):
            Driver.__download_driver(path, system)

        # we start at dl_try_count = 1 b/c we already downloaded the most recent version
        dl_try_count = 1
        cookie_try_count = 0
        MAX_TRIES = 3
        is_dl_success = False
        options = Driver.add_chrome_options(device, headless, cookies)

        while not is_dl_success:
            try:
                driver = webdriver.Chrome(path, options=options)
                is_dl_success = True

            #driver not up to date with Chrome browser, try different version
            except SessionNotCreatedException:
                if dl_try_count == MAX_TRIES:
                    raise SessionNotCreatedException(f'Tried downloading the {dl_try_count} most recent chromedrivers. None match your Chrome browswer version. Aborting now, please update your chrome browser.')
                Driver.__download_driver(path, system, dl_try_count)
                dl_try_count += 1

            except WebDriverException as wde:
                #Cookies option causing issues
                print(f'\nwebdriverexception msg: {str(wde)}')
                if "DevToolsActivePort file doesn't exist" in str(wde):
                    if cookie_try_count == 1:
                        raise WebDriverException('Driver cookie option issue?')
                    print('Trying chromedriver without cookies option')
                    options = Driver.add_chrome_options(device, headless, cookies=False)
                    cookie_try_count += 1
                else:
                    raise WebDriverException(wde.value)

        #if not headless:
        #    driver.set_window_position(-2000, 0)
        return EventFiringWebDriver(driver, EventListener())
