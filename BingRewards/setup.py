"""
Please read before editing: Any additional credential options
should be added to options.py inside parse_setup_args()

setup.py will simply parse these command line options.


Please note that the CWD is being changed below this is to ensure
1) setup.py can be run from any directory
2) options import don't fail.
Moved to Setup class so that there's no chdir during import
"""
import os
import sys
import json
import time
import copy
import base64
import getpass

CONFIG_DIR = "config/"
CONFIG_FILE = "config_multiple_accounts.json"
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)


def process_microsoft_account_args(args):
    """
    Convert argparse email list and password list
    into a list of dictionaries like so:

    [{
      "email": "abc@yahoo.com",
      "password": "123"
    },
    {
      "email": "def@gmail.com",
      "password": "234"
    }]
    """
    # https://stackoverflow.com/a/62887877
    return [
        {"email": zipped[0], "password": zipped[1]}
        for zipped in zip(args.email, args.password)
    ]


class Setup:
    credentials_template = {
        "microsoft_accounts": [],
        "discord_webhook_url": None,
        "telegram_userid": None,
        "telegram_api_token": None,
        "google_sheets_sheet_id": None,
        "google_sheets_tab_name": None,
    }

    def exit(self):
        """Unused currently"""
        print(
            f'\nYou already have a config file "{CONFIG_FILE_PATH}". You will'
            " need to:\n\n1. Edit config file directly\nOR\n2. Delete config"
            " file and re-run setup.py"
        )
        sys.exit("\nExiting setup.py now")

    def process_args(self, existing_credentials):
        from options import parse_setup_args

        new_credentials = copy.deepcopy(existing_credentials)
        args = parse_setup_args()
        if args.email:
            microsoft_accounts_args = process_microsoft_account_args(args)

            new_credentials["microsoft_accounts"] = (
                new_credentials["microsoft_accounts"] + microsoft_accounts_args
            )

        for arg_name, arg_value in vars(args).items():
            if arg_value:
                if arg_name not in ("email", "password"):
                    new_credentials[arg_name] = arg_value
        return new_credentials

    def __prompt_simple_input(self, existing_credentials):
        new_credentials = copy.deepcopy(existing_credentials)
        print(
            "\nEnter account(s) one at a time... "
            "\nTo finish, do NOT enter a value in the "
            "email prompt- just press <ENTER> key\n"
        )
        time.sleep(1.5)

        account_index = len(new_credentials["microsoft_accounts"]) + 1
        while True:
            entered_email = input(f"*MS Rewards Email {account_index}: ")
            if entered_email == "":
                break

            entered_pw = getpass.getpass(f"*Password {account_index}: ")

            account_dict = {"email": entered_email, "password": entered_pw}
            new_credentials["microsoft_accounts"].append(account_dict)
            account_index += 1
        return new_credentials

    def write_json(self, credentials):
        with open(CONFIG_FILE_PATH, "w") as f:
            json.dump(credentials, f, indent=4, sort_keys=True)
            print(f"\n{CONFIG_FILE} created/updated successfully")

    def main(self):
        """
        Creates/updates the config file.

        When no command line args, will prompt the user for
        their email / password.

        Otherwise, the commnad line arguments are used to update the config.

        Will only update:
        - the arguments specified by the user.
        - if the new values are different from the existing ones
        """

        # probably a better way of doing this,
        dir_run_from = os.getcwd()
        top_dir = os.path.dirname(sys.argv[0])
        if top_dir and top_dir != dir_run_from:
            os.chdir(top_dir)
        sys.path.append("BingRewards")

        deprecation = ConfigDeprecation()
        # config file exists
        if os.path.isfile(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH) as f:
                try:
                    existing_credentials = json.load(f)
                except ValueError:
                    existing_credentials = self.credentials_template

        else:  # config file doesn't exist
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)

            # port code over if config.json exists - v2
            if os.path.isfile(deprecation.DEPRECATED_CONFIG_FILE_PATH_JSON):
                ported_credentials = deprecation.port_json(self.credentials_template)
                self.write_json(ported_credentials)
                return

            # port code over if config.py exists - v1
            elif os.path.isfile(deprecation.DEPRECATED_CONFIG_FILE_PATH_PY):
                from src.config import credentials as ported_credentials

                self.write_json(ported_credentials)
                return

            else:  # no config to port over, instantiate using template
                existing_credentials = self.credentials_template

        args = sys.argv
        # prompt input from user
        if len(args) == 1:
            new_credentials = self.__prompt_simple_input(existing_credentials)

        else:  # user passed in cmd line args, parse args
            new_credentials = self.process_args(existing_credentials)
        if new_credentials != existing_credentials:
            self.write_json(new_credentials)
        else:
            print(f"\n{CONFIG_FILE_PATH} already contains latest credentials")


class ConfigDeprecation:
    """Class to handle any config deprecations"""

    DEPRECATED_CONFIG_FILE_PATH_PY = os.path.join("BingRewards/src/config.py")
    DEPRECATED_CONFIG_FILE_PATH_JSON = os.path.join("config/config.json")

    def __decode(self, encoded):
        if encoded:
            return base64.b64decode(encoded).decode()

    def port_json(self, credentials_template):
        """
        When converting to multiple accounts json
        Port over existing simple json file
        """
        microsoft_account = dict()

        new_credentials = copy.deepcopy(credentials_template)

        with open(self.DEPRECATED_CONFIG_FILE_PATH_JSON) as f:
            old_json = json.load(f)

        for k, v in old_json.items():
            if k not in ("email", "password"):
                new_credentials[k] = self.__decode(v)
            else:
                microsoft_account[k] = self.__decode(v)
        new_credentials["microsoft_accounts"].append(microsoft_account)
        return new_credentials


if __name__ == "__main__":
    setup = Setup()
    setup.main()
