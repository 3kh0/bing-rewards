from abc import ABC, abstractmethod
import os
import platform

import urllib
import requests
import ssl
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.support.abstract_event_listener import (
    AbstractEventListener,
)
from selenium.webdriver.support.event_firing_webdriver import (
    EventFiringWebDriver,
)
from selenium.common.exceptions import (
    SessionNotCreatedException,
    WebDriverException,
)
import re
import random
import string


class EventListener(AbstractEventListener):
    """Attempt to disable animations"""

    def after_click(self, url, driver):
        animation = r"try { jQuery.fx.off = true; } catch(e) {}"
        driver.execute_script(animation)


class Driver(EventFiringWebDriver):
    def __init__(self, driver, EventListener, device):
        super().__init__(driver, EventListener)
        self.device = device

    def close_other_tabs(self):
        """Closes all but current tab"""
        curr = self.current_window_handle
        for handle in self.window_handles:
            self.switch_to.window(handle)
            if handle != curr:
                self.close()
        self.switch_to.window(curr)

    def switch_to_n_tab(self, n):
        self.switch_to.window(self.window_handles[n])

    def switch_to_first_tab(self):
        self.switch_to_n_tab(0)

    def switch_to_last_tab(self):
        self.switch_to_n_tab(-1)


class DriverFactory(ABC):
    WEB_DEVICE = "web"
    MOBILE_DEVICE = "mobile"
    DRIVERS_DIR = "drivers"

    # Microsoft Edge user agents for additional points
    # https://www.whatismybrowser.com/guides/the-latest-user-agent/edge
    __WEB_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.57"
    )
    __MOBILE_USER_AGENT = (
        "Mozilla/5.0 (Linux; Android 10; HD1913) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/110.0.5481.153 Mobile Safari/537.36"
        " EdgA/110.0.1587.50"
    )
    MAX_DOWNLOAD_ATTEMPTS = 4

    @property
    @staticmethod
    @abstractmethod
    def VERSION_MISMATCH_STR():
        pass

    @property
    @staticmethod
    @abstractmethod
    def WebDriverCls():
        pass

    @property
    @staticmethod
    @abstractmethod
    def WebDriverOptions():
        pass

    @property
    @staticmethod
    @abstractmethod
    def driver_name():
        pass

    @staticmethod
    @abstractmethod
    def _get_latest_driver_url(dl_try_count):
        raise NotImplementedError

    def replace_selenium_marker(driver_path):
        os_with_perl = ("Linux", "Darwin")  # MacOS
        if platform.system() not in os_with_perl:
            return

        letters = string.ascii_lowercase
        cdc_replacement = "".join(random.choice(letters) for i in range(3)) + "_"
        perl_command = f"perl -pi -e 's/cdc_/{cdc_replacement}/g' {driver_path}"

        try:
            os.system(perl_command)
            print(
                'Sucessfully replaced driver string "cdc_" with'
                f' "{cdc_replacement}"\n'
            )
        except Exception as e:
            print(
                "Unable to replace selenium cdc_ string due to exception. No"
                " worries, program should still work without string"
                f" replacement.\n{e}."
            )

    @classmethod
    def __download_driver(cls, dl_try_count=0):
        url = cls._get_latest_driver_url(dl_try_count)

        try:
            response = urllib.request.urlopen(
                url, context=ssl.SSLContext(ssl.PROTOCOL_TLS)
            )  # context args for mac
        except ssl.SSLError:
            response = urllib.request.urlopen(url)  # context args for mac
        zip_file_path = os.path.join(cls.DRIVERS_DIR, os.path.basename(url))
        with open(zip_file_path, "wb") as zip_file:
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break
                zip_file.write(chunk)

        extracted_dir = os.path.splitext(zip_file_path)[0]
        with zipfile.ZipFile(zip_file_path, "r") as zip_file:
            zip_file.extractall(extracted_dir)
        os.remove(zip_file_path)

        driver_path = os.path.join(cls.DRIVERS_DIR, cls.driver_name)
        try:
            os.rename(os.path.join(extracted_dir, cls.driver_name), driver_path)
        # for Windows
        except FileExistsError:
            os.replace(os.path.join(extracted_dir, cls.driver_name), driver_path)

        shutil.rmtree(extracted_dir)
        os.chmod(driver_path, 0o755)

        # removing because -nhl mode no longer works with this
        # if cls.WebDriverCls == webdriver.Chrome:
        #    cls.replace_selenium_marker(driver_path)

    @classmethod
    def add_driver_options(cls, device, headless, cookies, nosandbox):
        options = cls.WebDriverOptions()

        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1280,1024")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-notifications")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")

        options.add_experimental_option(
            "prefs",
            {
                # geolocation permission, 0=Ask, 1=Allow, 2=Deny
                "profile.default_content_setting_values.geolocation": 1,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.images": 2,
            },
        )

        if headless:
            options.add_argument("--headless")

        if device == cls.WEB_DEVICE:
            options.add_argument("user-agent=" + cls.__WEB_USER_AGENT)
        else:
            options.add_argument("user-agent=" + cls.__MOBILE_USER_AGENT)

        if cookies:
            cookies_path = os.path.join(os.getcwd(), "stored_browser_data/")
            options.add_argument("user-data-dir=" + cookies_path)

        if nosandbox:
            options.add_argument("--no-sandbox")

        return options

    @classmethod
    def get_driver(cls, device, headless, cookies, nosandbox) -> Driver:
        dl_try_count = 0
        options = cls.add_driver_options(device, headless, cookies, nosandbox)

        # raspberry pi: assumes driver preinstalled by user
        if platform.machine() in ["armv7l", "aarch64"]:
            driver_path = "/usr/lib/chromium-browser/chromedriver"
        # all other platforms, install driver ourselves
        else:
            if not os.path.exists(cls.DRIVERS_DIR):
                os.mkdir(cls.DRIVERS_DIR)
            driver_path = os.path.join(cls.DRIVERS_DIR, cls.driver_name)

        # Instantiate and if necessary, download new driver
        while True:
            # Try instantiating a driver
            # Instantiate before dling bc driver may already exist
            try:
                if os.path.exists(driver_path):
                    driver = cls.WebDriverCls(driver_path, options=options)
                    return Driver(driver, EventListener(), device)

            except SessionNotCreatedException as se:
                error_msg = str(se).lower()
                if cls.VERSION_MISMATCH_STR in error_msg:
                    print(
                        "The downloaded driver does not match your browser"
                        " version...\n"
                    )
                else:  # other exc besides mismatching ver
                    raise SessionNotCreatedException(error_msg)

            # WebDriverException is Selenium generic exception
            except WebDriverException as wde:
                error_msg = str(wde)
                print(f"\nerror_msg: {error_msg}")

                # handle cookie error
                if "DevToolsActivePort file doesn't exist" in error_msg:
                    print(
                        "Possibly due to driver error using cookies option."
                        "Trying without cookies."
                    )
                    options = cls.add_driver_options(
                        device, headless, cookies=False, nosandbox=nosandbox
                    )

                else:
                    raise WebDriverException(error_msg)

            # Try downloading driver
            try:
                if dl_try_count >= cls.MAX_DOWNLOAD_ATTEMPTS:
                    raise SessionNotCreatedException(
                        f"Tried downloading the {dl_try_count} most recent"
                        " drivers. None match your browser version. Aborting"
                        " now, please update your browser."
                    )
                cls.__download_driver(dl_try_count)
            except urllib.error.HTTPError:
                print(
                    "Download page does not exist for this version/platform" " combo."
                )
            dl_try_count += 1


class ChromeDriverFactory(DriverFactory):
    WebDriverCls = webdriver.Chrome
    WebDriverOptions = webdriver.ChromeOptions
    VERSION_MISMATCH_STR = "this version of chromedriver only supports chrome version"
    driver_name = (
        "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
    )

    def _get_latest_driver_url(dl_try_count):
        # determine latest chromedriver version
        CHROME_RELEASE_URL = (
            "https://sites.google.com/chromium.org/driver/downloads?authuser=0"
        )
        response = requests.get(CHROME_RELEASE_URL).content

        version_regex = r"ChromeDriver \d{2,3}\.0\.\d{4}\.\d+"
        latest_version = re.findall(f"{version_regex}", str(response))[
            dl_try_count
        ].split()[1]
        print(
            f"\nDownloading {platform.system()} chromedriver version:"
            f" {latest_version}"
        )

        system = platform.system()
        if system == "Windows":
            url = (
                "https://chromedriver.storage.googleapis.com/"
                f"{latest_version}/chromedriver_win32.zip"
            )
        elif system == "Darwin":
            # M1
            if platform.processor() == "arm":
                url = (
                    "https://chromedriver.storage.googleapis.com/"
                    f"{latest_version}/chromedriver_mac_arm64.zip"
                )
            else:
                url = (
                    "https://chromedriver.storage.googleapis.com/"
                    f"{latest_version}/chromedriver_mac64.zip"
                )
        elif system == "Linux":
            url = (
                "https://chromedriver.storage.googleapis.com/"
                f"{latest_version}/chromedriver_linux64.zip"
            )
        return url


class MsEdgeDriverFactory(DriverFactory):
    WebDriverCls = webdriver.Edge
    WebDriverOptions = webdriver.EdgeOptions
    VERSION_MISMATCH_STR = (
        "this version of microsoft edge webdriver only supports microsoft edge"
        " version"
    )
    driver_name = (
        "msedgedriver.exe" if platform.system() == "Windows" else "msedgedriver"
    )

    @staticmethod
    def get_major_edge_driver_versions(all_versions):
        """
        The MS driver page includes all minor versions, i.e
        110.0.1587.0, 110.0.1586.0, 110.0.1585.0
        109.0.1518.8, 109.0.1518.26, 109.0.1518.23

        This function returns only the greatest major versions:
        110.0.1587.0, 109.0.1518.8
        """
        major_versions = []
        latest_major_version_num = "100"
        for current_version in all_versions:
            current_version_num = current_version.split()[1]
            current_major_version_num = current_version_num.split(".")[0]
            if current_major_version_num != latest_major_version_num:
                major_versions.append(current_version_num)
                latest_major_version_num = current_major_version_num
        # remove the latest (dev) version, it's limited
        # major_versions = major_versions[1:]
        return sorted(major_versions, reverse=True)

    def _get_latest_driver_url(dl_try_count):
        EDGE_RELEASE_URL = (
            "https://developer.microsoft.com/en-us/" "microsoft-edge/tools/webdriver/"
        )
        response = requests.get(EDGE_RELEASE_URL).content

        version_regex = r"Version: \d{2,3}\.0\.\d{4}\.\d+"
        all_versions = sorted(
            list(set(re.findall(version_regex, str(response)))),
            reverse=True,
        )
        major_versions = MsEdgeDriverFactory.get_major_edge_driver_versions(
            all_versions
        )

        latest_version = major_versions[dl_try_count]
        print(
            f"\nDownloading {platform.system()} msedgedriver version:"
            f" {latest_version}"
        )

        system = platform.system()

        if system == "Windows":
            url = (
                f"https://msedgedriver.azureedge.net/{latest_version}/"
                "edgedriver_win64.zip"
            )
        elif system == "Darwin":
            # M1
            if platform.processor() == "arm":
                url = (
                    f"https://msedgedriver.azureedge.net/{latest_version}/"
                    "edgedriver_mac64_m1.zip"
                )
            else:
                url = (
                    f"https://msedgedriver.azureedge.net/{latest_version}/"
                    "edgedriver_mac64.zip"
                )
        elif system == "Linux":
            url = (
                f"https://msedgedriver.azureedge.net/{latest_version}/"
                "edgedriver_linux64.zip"
            )
        return url
