import argparse
import getpass
import selenium
import sys
from src.driver import ChromeDriver, MsEdgeDriver


class PasswordAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            print(
                '\nWarning: User set the password in plain text. Use `-p` with no arguments next time for better security.\n'
            )
            setattr(namespace, self.dest, values)
        else:
            setattr(namespace, self.dest, getpass.getpass())


class DriverAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        mapping = {"chrome": ChromeDriver,
                   "msedge": MsEdgeDriver}
        if value == "msedge" and int(selenium.__version__.split('.')[0]) < 4:
            print("Microsoft Edge is only supported on selenium 4 and above\nRun 'pip install -U selenium' to update", file=sys.stderr)
            sys.exit(-1)
        setattr(namespace, self.dest, mapping[value])


def print_args(args):
    d_args = vars(args).copy()
    del (d_args['password'])
    result = ", ".join(
        str(key) + '=' + str(value) for key, value in d_args.items()
    )

    print(f'\nCommand line options selected:\n{result}\n')


def parse_arguments():
    '''
    Search options satisfy this criteria:
    One- and only one- of the args in the search_group must be used
    Source: https://stackoverflow.com/a/15301183

    Email and pw, using getpass, https://stackoverflow.com/a/28610617

    Headless, https://stackoverflow.com/a/15008806
    '''
    # main search arguments
    parser = argparse.ArgumentParser()

    search_group = parser.add_mutually_exclusive_group()
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

    headless_group = parser.add_mutually_exclusive_group()
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

    parser.add_argument(
        '-e', '--email', help='email to use, supersedes the config email'
    )
    parser.add_argument(
        '-p',
        '--password',
        action=PasswordAction,
        nargs='?',
        help="the email password to use. Use -p with no argument to trigger a secure pw prompt"
    )

    cookies_group = parser.add_mutually_exclusive_group()
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

    telegram_group = parser.add_mutually_exclusive_group()
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
    parser.add_argument(
        '-d',
        '--driver',
        dest='driver',
        type=str.lower,
        choices=['chrome', 'msedge'],
        action=DriverAction
    )

    parser.set_defaults(search_type='remaining', headless=True,
                        cookies=False, telegram=True, driver=ChromeDriver)

    args = parser.parse_args()

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
    print_args(args)
    return args


if __name__ == '__main__':
    args = parse_arguments()
