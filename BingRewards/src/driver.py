import os
import platform
from urllib.request import urlopen
import ssl
import zipfile
from selenium import webdriver
from selenium.webdriver.support.abstract_event_listener import AbstractEventListener
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebDriver
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
    WEB_DEVICE                  = 0
    MOBILE_DEVICE               = 1

    # Microsoft Edge user agents for additional points
    #agent src: https://www.whatismybrowser.com/guides/the-latest-user-agent/edge
    __WEB_USER_AGENT            = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 Edg/88.0.705.63"
    __MOBILE_USER_AGENT         = "Mozilla/5.0 (Linux; Android 10; HD1913) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Mobile Safari/537.36 EdgA/46.1.2.5140"


    def __download_driver(driver_path, system, driver_dl_index=0):
        # determine latest chromedriver version
        #version selection faq: http://chromedriver.chromium.org/downloads/version-selection
        try:
            response = urlopen("https://sites.google.com/a/chromium.org/chromedriver/downloads", context=ssl.SSLContext(ssl.PROTOCOL_TLSv1)).read()
        except ssl.SSLError as e:
            response = urlopen("https://sites.google.com/a/chromium.org/chromedriver/downloads").read()
        #download second latest version,most recent is sometimes not out to public yet

        latest_version = re.findall(b"ChromeDriver \d{2,3}\.0\.\d{4}\.\d+",response)[driver_dl_index].decode().split()[1]
        print('downloading chrome driver version: ' + latest_version)

        if system == "Windows":
            url = "https://chromedriver.storage.googleapis.com/{}/chromedriver_win32.zip".format(latest_version)
        elif system == "Darwin":
            url = "https://chromedriver.storage.googleapis.com/{}/chromedriver_mac64.zip".format(latest_version)
        elif system == "Linux":
            url = "https://chromedriver.storage.googleapis.com/{}/chromedriver_linux64.zip".format(latest_version)

        try:
            response = urlopen(url, context=ssl.SSLContext(ssl.PROTOCOL_TLSv1)) # context args for mac
        except ssl.SSLError as e:
            response = urlopen(url)# context args for mac
        zip_file_path = os.path.join(os.path.dirname(driver_path), os.path.basename(url))
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

    def get_driver(path, device, headless):
        system = platform.system()
        if system == "Windows":
            if not path.endswith(".exe"):
                path += ".exe"
        if not os.path.exists(path):
            Driver.__download_driver(path, system)

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1280,1024")
        options.add_argument("--log-level=3")
        options.add_experimental_option("prefs", {"profile.default_content_setting_values.geolocation" : 1}) # geolocation permission, 0=Ask, 1=Allow, 2=Deny
        if headless:
            options.add_argument("--headless")
        #else:
        #    options.add_argument("--window-position=-2000,0") # doesnt move off screen

        if device == Driver.WEB_DEVICE:
            options.add_argument("user-agent=" + Driver.__WEB_USER_AGENT)
        else:
            options.add_argument("user-agent=" + Driver.__MOBILE_USER_AGENT)

        driver_dl_index = 1
        while True:
            try:
                driver = webdriver.Chrome(path, options=options)
                break
            #driver not up to date with Chrome browser, try different ver
            except:
                Driver.__download_driver(path, system, driver_dl_index)
                driver_dl_index += 1
                if driver_dl_index > 2:
                    print('Tried downloading the ' + str(driver_dl_index) + ' most recent chrome drivers. None match current Chrome browser version')
                    break

        #if not headless:
        #    driver.set_window_position(-2000, 0)
        return EventFiringWebDriver(driver, EventListener())
