"""
Please read before editing: Any additional credential options should be added to options.py inside parse_setup_args()

setup.py will simply parse these command line options.
"""
import os
import getpass
import base64
import sys
import json

#probably a better way of doing this, this is to ensure 1) setup.py can be run from any directory 2) options import don't fail
dir_run_from = os.getcwd()
top_dir = os.path.dirname(sys.argv[0])
if top_dir and top_dir != dir_run_from:
    os.chdir(top_dir)
sys.path.append('BingRewards')
from options import parse_setup_args

CONFIG_DIR = 'config/'
CONFIG_FILE = "config.json"
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)
DEPRECATED_CONFIG_FILE_PATH = os.path.join("BingRewards/src/config.py")


def __encode(s):
    return base64.b64encode(s.encode()).decode()


def __get_args(existing_credentials):
    new_credentials = existing_credentials.copy()
    args = parse_setup_args()
    for arg_name, arg_value in vars(args).items():
        if arg_value:
            new_credentials[arg_name] = __encode(arg_value)
    return new_credentials


def __prompt_simple_input(existing_credentials):
    new_credentials = existing_credentials.copy()
    email = __encode(input("*MS Rewards Email: "))
    password = __encode(getpass.getpass("*Password: "))

    new_credentials['email'] = email
    new_credentials['password'] = password
    return new_credentials


def write(credentials):
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

        #port code over if `config.py` exists
        if os.path.isfile(DEPRECATED_CONFIG_FILE_PATH):
            from src.config import credentials
            write(credentials)
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
        write(new_credentials)
    else:
        print(f"\n{CONFIG_FILE_PATH} already contains latest credentials")


if __name__ == "__main__":
    main()
