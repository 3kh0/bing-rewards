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
    __WEB_USER_AGENT            = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.48 Safari/537.36 Edg/74.1.96.24"
    __MOBILE_USER_AGENT         = "Mozilla/5.0 (Linux; Android 7.1.1; Moto G Play) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.83 Mobile Safari/537.36"
    #__MOBILE_USER_AGENT         = "Mozilla/5.0 (Linux; Android 8.0; Pixel XL Build/OPP3.170518.006) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.0 Mobile Safari/537.36 EdgA/41.1.35.1"


    def __download_driver(driver_path, system, driver_dl_index=1):
        # determine latest chromedriver version
        #version selection faq: http://chromedriver.chromium.org/downloads/version-selection
        response = urlopen("https://sites.google.com/a/chromium.org/chromedriver/downloads", context=ssl.SSLContext(ssl.PROTOCOL_TLSv1)).read()
        #download second latest version,most recent is sometimes not out to public yet
        latest_version = re.findall(b"ChromeDriver \d+\.\d+\.\d+\.\d+",response)[driver_dl_index].decode().split()[1]
        print('downloading chrome driver version: ' + latest_version)

        if system == "Windows":
            url = "https://chromedriver.storage.googleapis.com/{}/chromedriver_win32.zip".format(latest_version)
        elif system == "Darwin":
            url = "https://chromedriver.storage.googleapis.com/{}/chromedriver_mac64.zip".format(latest_version)

        response = urlopen(url, context=ssl.SSLContext(ssl.PROTOCOL_TLSv1)) # context args for mac
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
        
        driver_dl_index = 2
        while True:
            try:
                driver = webdriver.Chrome(path, chrome_options=options)
                break
            #driver not up to date with Chrome browswer
            except:
                Driver.__download_driver(path, system, driver_dl_index)
            if driver_dl_index < 0:
                print('Tried downloading the ' + str(driver_dl_index + 1) + ' most recent chrome drivers. None match current Chrome browser version')
                break
            driver_dl_index -= 1

        #if not headless:
        #    driver.set_window_position(-2000, 0)
        return EventFiringWebDriver(driver, EventListener())
    def close(driver):
        # close open tabs
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            driver.close()

