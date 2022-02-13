import os
import getpass
import base64
import time


def encode_input(s):
    return base64.b64encode(s.encode()).decode()


def use_old_or_new(prev_val, new_val):
    '''
    Use the new inputted value if the user didn't skip input
    Else just use the old one
    '''
    if new_val:
        return new_val
    return prev_val


def update_value(input_value, attribute_type):
    old_value = credentials.get(attribute_type)
    new_value = encode_input(input_value)
    final_value = use_old_or_new(old_value, new_value)
    print(f"   Hashed: {final_value}\n")
    return final_value


CONFIG_FILE_PATH = "BingRewards/src/config.py"
CONFIG_FILE_TEMPLATE = """credentials = dict(
    email = '{0}',
    password = '{1}',
    telegram_api_token = '{2}',
    telegram_userid = '{3}'
)
"""

if os.path.isfile(CONFIG_FILE_PATH):
    from BingRewards.src.config import credentials
else:
    credentials = {}

print('Note: To SKIP a field, press <ENTER>. If skipped, will use current value if it exists.\n')

email = update_value(input("*MS Rewards Email: "), 'email')
password = update_value(getpass.getpass("*Password: "), 'password')

telegram_api_token = update_value(input("*Telegram API Token (optional)"), 'telegram_api_token')
telegram_userid = update_value(input("*Telegram User ID (optional)"), 'telegram_userid')

new_config = CONFIG_FILE_TEMPLATE.format(email, password, telegram_api_token, telegram_userid)

# check if config file exists
if not os.path.isfile(CONFIG_FILE_PATH):
    # create new config file
    with open(CONFIG_FILE_PATH, "w") as config_file:
        config_file.write(new_config)
        print("{} created successfully".format(CONFIG_FILE_PATH))
else:
    with open(CONFIG_FILE_PATH, "r") as config_file:
        cur_config = config_file.read()
    if new_config != cur_config:
        # update config file
        with open(CONFIG_FILE_PATH, "w") as config_file:
            config_file.writelines(new_config)
        print("{} updated successfully".format(CONFIG_FILE_PATH))
    else:
        print("{} already contains latest credentials".format(CONFIG_FILE_PATH))
time.sleep(2)
