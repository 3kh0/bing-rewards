import os
import getpass
import base64
import time

CONFIG_FILE_PATH = "BingRewards/src/config.py"

CONFIG_FILE_TEMPLATE = """credentials = dict(
    email = '{0}',
    password = '{1}',
    telegram_api_token = '{2}',
    telegram_userid = '{3}'
)
"""


def encode_input(s):
    return base64.b64encode(s.encode()).decode()


# get hashed credentials
email = encode_input(input("   *Email: "))
print(f"   Hashed: {email}\n")
password = encode_input(getpass.getpass("*Password: "))
print(f"   Hashed: {password}\n")

telegram_api_token = encode_input(input("*Telegram API Token (optional, press enter to skip): "))
print(f"   Hashed: {telegram_api_token}\n")
telegram_userid = encode_input(input("*Telegram User ID (optional, press enter to skip): "))
print(f"   Hashed: {telegram_userid}\n")

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
