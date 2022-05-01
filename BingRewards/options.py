import argparse
import getpass
from src.driver import ChromeDriverFactory, MsEdgeDriverFactory


class PasswordAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            print(
                '\nWarning: User set the password in plain text. Use `-p` with no arguments next time for better security.'
            )
            setattr(namespace, self.dest, values)
        else:
            prompt = f'{option_string}:'
            setattr(namespace, self.dest, getpass.getpass(prompt=prompt))


class DriverAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        mapping = {"chrome": ChromeDriverFactory, "msedge": MsEdgeDriverFactory}
        setattr(namespace, self.dest, mapping[value])


def print_args(args):
    protected_fields = ('password', 'telegram_api_token')
    d_args = vars(args).copy()
    for protected_field in protected_fields:
        if protected_field in d_args:
            del (d_args[protected_field])
    result = ", ".join(
        str(key) + '=' + str(value) for key, value in d_args.items()
    )

    print(f'\nCommand line options selected:\n{result}')


def check_is_valid_email_pw_combo(args):
    if (args.email and not args.password) or (not args.email and args.password):
        if args.email:
            included_arg = 'email'
            missing_arg = 'password'
        else:
            included_arg = 'password'
            missing_arg = 'email'
        raise RuntimeError(
            f'Missing {missing_arg} argument. You included {included_arg} argument, you must also include {missing_arg} argument.'
        )


def get_parent_parser():
    ''' parent parser - store default args '''
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '-e', '--email', help='email to use, supersedes the config email'
    )
    parent_parser.add_argument(
        '-p',
        '--password',
        action=PasswordAction,
        nargs='?',
        help=
        "the email password to use. Use -p with no argument to trigger a secure pw prompt"
    )
    return parent_parser


def parse_setup_args():
    ''' Responsible for parsing setup.py args '''
    # main search arguments
    parent_parser = get_parent_parser()
    setup_parser = argparse.ArgumentParser(parents=[parent_parser])

    # telegram config
    setup_parser.add_argument(
        '-tu', '--telegram_userid', help='telegram userid to store in config'
    )
    setup_parser.add_argument(
        '-ta',
        '--telegram_api_token',
        action=PasswordAction,
        nargs='?',
        help=
        "telegram api token to store in config, use with no argument to trigger a secure prompt",
    )
    args = setup_parser.parse_args()
    check_is_valid_email_pw_combo(args)
    print_args(args)
    return args


def parse_search_args():
    '''
    Search options satisfy this criteria:
    One- and only one- of the args in the search_group must be used
    Source: https://stackoverflow.com/a/15301183

    Email and pw, using getpass, https://stackoverflow.com/a/28610617

    Headless, https://stackoverflow.com/a/15008806
    '''
    # main search arguments
    parent_parser = get_parent_parser()
    search_parser = argparse.ArgumentParser(parents=[parent_parser])

    search_group = search_parser.add_mutually_exclusive_group()
    search_group.add_argument(
        '-r',
        '--remaining',
        const='remaining',
        action='store_const',
        dest='search_type',
        help="run today's remaining searches, this is the default search type"
    )
    search_group.add_argument(
        '-w',
        '--web',
        const='web',
        action='store_const',
        dest='search_type',
        help='run web search'
    )
    search_group.add_argument(
        '-m',
        '--mobile',
        const='mobile',
        action='store_const',
        dest='search_type',
        help='run mobile search'
    )
    search_group.add_argument(
        '-b',
        '--both',
        const='both',
        action='store_const',
        dest='search_type',
        help='run web and mobile search'
    )
    search_group.add_argument(
        '-o',
        '--offers',
        const='offers',
        action='store_const',
        dest='search_type',
        help='run offers'
    )
    search_group.add_argument(
        '-pc',
        '--punchcard',
        const='punch card',
        action='store_const',
        dest='search_type',
        help='run punch card'
    )
    search_group.add_argument(
        '-a',
        '--all',
        const='all',
        action='store_const',
        dest='search_type',
        help='run web, mobile, offers, and punch cards'
    )

    headless_group = search_parser.add_mutually_exclusive_group()
    headless_group.add_argument(
        '-hl',
        '--headless',
        dest='headless',
        action='store_true',
        help='run in headless mode, this is the default'
    )
    headless_group.add_argument(
        '-nhl',
        '--no-headless',
        dest='headless',
        action='store_false',
        help='run in non-headless mode'
    )

    cookies_group = search_parser.add_mutually_exclusive_group()
    cookies_group.add_argument(
        '-c',
        '--cookies',
        dest='cookies',
        action='store_true',
        help='run browser with cookies, this is the default'
    )
    cookies_group.add_argument(
        '-nc',
        '--no-cookies',
        dest='cookies',
        action='store_false',
        help='run browser without cookies'
    )

    telegram_group = search_parser.add_mutually_exclusive_group()
    telegram_group.add_argument(
        '-t',
        '--telegram',
        dest='telegram',
        action='store_true',
        help='send notification to telegram using setup.py credentials, this is the default'
    )
    telegram_group.add_argument(
        '-nt',
        '--no-telegram',
        dest='telegram',
        action='store_false',
        help='do not send notifications to telegram'
    )

    google_spreadsheet_group = search_parser.add_mutually_exclusive_group()
    google_spreadsheet_group.add_argument(
        '-gs',
        '--googlespreadsheet',
        dest='googlespreadsheet',
        action='store_true',
        help='add row to existing Google Spreadsheet using setup.py credentials'
    )
    google_spreadsheet_group.add_argument(
        '-ngs',
        '--no-googlespreadsheet',
        dest='googlespreadsheet',
        action='store_false',
        help='do not add row to existing Google Spreadsheet, this is the default'
    )

    search_parser.add_argument(
        '-d',
        '--driver',
        dest='driver',
        type=str.lower,
        choices=['chrome', 'msedge'],
        action=DriverAction
    )

    search_parser.set_defaults(
        search_type='remaining',
        headless=True,
        cookies=False,
        telegram=True,
        google_spreadsheet=False,
        driver=ChromeDriverFactory
    )

    args = search_parser.parse_args()
    check_is_valid_email_pw_combo(args)

    print_args(args)
    return args


if __name__ == '__main__':
    args = parse_search_args()
