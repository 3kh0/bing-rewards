"""
Please read before editing: Any additional credential options should be added to options.py inside parse_setup_args()

setup.py will simply parse these command line options.
"""
import os
import sys
import json
import base64

#probably a better way of doing this, this is to ensure 1) setup.py can be run from any directory 2) options import don't fail
dir_run_from = os.getcwd()
top_dir = os.path.dirname(sys.argv[0])
if top_dir and top_dir != dir_run_from:
    os.chdir(top_dir)
sys.path.append('BingRewards')
from options import parse_setup_args

CONFIG_DIR = 'config/'
CONFIG_FILE = "config_multiple_accounts.json"
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)


def __get_args(existing_credentials):
    new_credentials = existing_credentials.copy()
    args = parse_setup_args()
    for arg_name, arg_value in vars(args).items():
        if arg_value:
            new_credentials[arg_name] = arg_value
    return new_credentials


def __prompt_simple_input(existing_credentials):
    new_credentials = existing_credentials.copy()
    new_credentials['email'] = input("*MS Rewards Email: ")
    new_credentials['password'] = input("*Password: ")
    return new_credentials


def write_json(credentials):
    with open(CONFIG_FILE_PATH, "w") as f:
        json.dump(credentials, f, indent=4, sort_keys=True)
        print(f"\n{CONFIG_FILE} created/updated successfully")


def main():
    """
    Creates/updates the config file.

    When no command line args, will prompt the user for their email / password.

    Otherwise, the commnad line arguments are used to update the config.

    Will only update:
    - the arguments specified by the user.
    - if the new values are different from the existing ones
    """
    deprecation = ConfigDeprecation()
    # json config file exists
    if os.path.isfile(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH) as f:
            try:
                existing_credentials = json.load(f)
                if existing_credentials is None:
                    existing_credentials = {}
            except ValueError:
                existing_credentials = {}

    else:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)

        #port code over if config.json exists - v2
        if os.path.isfile(deprecation.DEPRECATED_CONFIG_FILE_PATH_JSON):
            ported_credentials = deprecation.port_json()
            write_json(ported_credentials)
            return

        #port code over if config.py exists - v1
        elif os.path.isfile(deprecation.DEPRECATED_CONFIG_FILE_PATH_PY):
            from src.config import credentials as ported_credentials
            write_json(ported_credentials)
            return

        else:
            existing_credentials = {}

    args = sys.argv
    # prompt input from user
    if len(args) == 1:
        new_credentials = __prompt_simple_input(existing_credentials)
    # get via command line args
    else:
        new_credentials = __get_args(existing_credentials)
    if new_credentials != existing_credentials:
        write_json(new_credentials)
    else:
        print(f"\n{CONFIG_FILE_PATH} already contains latest credentials")


class ConfigDeprecation():
    """ Class to handle any config deprecations
    """
    DEPRECATED_CONFIG_FILE_PATH_PY = os.path.join("BingRewards/src/config.py")
    # DEPRECATED_CONFIG_FILE_PATH_JSON = os.path.join("BingRewards/config/config.json")
    DEPRECATED_CONFIG_FILE_PATH_JSON = os.path.join("config/config.json")

    def __decode(self, encoded):
        if encoded:
            return base64.b64decode(encoded).decode()

    def port_json(self):
        """
        When converting to multiple accounts json
        Port over existing simple json file
        """
        microsoft_account = dict()
        credentials_template = {
            "microsoft_accounts": [],
            "discord_webhook_url": None,
            "telegram_userid": None,
            "telegram_api_token": None,
            "google_sheets_sheet_id": None,
            "google_sheets_tab_name": None,
            "max_attempts_per_account": 2,
        }
        new_credentials = credentials_template.copy()

        with open(self.DEPRECATED_CONFIG_FILE_PATH_JSON) as f:
            old_json = json.load(f)

        for k, v in old_json.items():
            if k not in ('email', 'password'):
                new_credentials[k] = self.__decode(v)
            else:
                microsoft_account[k] = self.__decode(v)
        new_credentials['microsoft_accounts'].append(microsoft_account)
        return new_credentials


if __name__ == "__main__":
    main()
