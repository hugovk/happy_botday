#!/usr/bin/env python
# encoding: utf-8
"""
Tweet birthday wishes for bots created today!
"""
from __future__ import print_function, unicode_literals

# from pprint import pprint
from twitter import Twitter, OAuth  # pip install twitter

import argparse
import inflect  # pip install inflect
import random
import time
import webbrowser
import yaml  # pip install pyyaml


TWITTER = None

GREETS = [
    "Happy {0} birthday to @{1}! {2} #happybotday",
    "Happy {0} birthday @{1}! {2} #happybotday",
    "Happy {0} birthday, @{1}! {2} #happybotday",
    "Congratulations to @{1} on your {0} birthday! {2} #happybotday",
    "{0} birthday wishes @{1}! {2} #happybotday",
    "It's @{1}'s {0} birthday! {2} #happybotday",
    "Three cheers for @{1}'s {0} birthday! {2} #happybotday",
    ".@{1}, it's your {0} birthday! {2} #happybotday",
]

# fmt: off
EMOJI = [
    "😀", "😃", "😄", "😊", "😋", "😎", "☺", "🙂", "🤗", "😺", "😸",
    "💃", "👍", "👏", "✌",
    "🎂", "🍰", "🍩", "🍨", "🍦", "🍫", "🍬", "🍭",
    "🍮", "🍾", "🍷", "🍸", "🍹", "🍺", "🍻",
    "🎈", "🎉", "🎁", "🕯", "🙌",
]
# fmt: on


def print_it(text):
    """cmd.exe cannot do Unicode so encode first"""
    print(text.encode("utf-8"))


def timestamp():
    """ Print a timestamp and the filename with path """
    import datetime

    print(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p") + " " + __file__)


def load_yaml(filename):
    """
    File should contain:
    consumer_key: TODO_ENTER_YOURS
    consumer_secret: TODO_ENTER_YOURS
    AND (
    access_token: TODO_ENTER_YOURS
    access_token_secret: TODO_ENTER_YOURS
        OR
    oauth_token: TODO_ENTER_YOURS
    oauth_token_secret: TODO_ENTER_YOURS
    )
    """
    with open(filename) as f:
        data = yaml.safe_load(f)

    return data


def get_list_members(list_owner, list_name):
    # print("GET lists/members")
    # https://dev.twitter.com/rest/reference/get/lists/members

    # Page 1
    cursor = -1

    all_users = []

    while cursor != 0:
        # print("Cursor:", cursor)
        users = TWITTER.lists.members(
            owner_screen_name=list_owner,
            slug=list_name,
            cursor=cursor,
            include_user_entities=False,
            skip_status=True,
            count=5000,
        )
        cursor = users["next_cursor"]
        all_users.extend(users["users"])

    return all_users


def created_at_timestamp(user):
    """Return Twitter format 'Thu May 15 02:33:11 +0000 2014'
     as Python timestamp
     """
    return time.strftime(
        "%Y-%m-%d %H:%M:%S",
        time.strptime(user["created_at"], "%a %b %d %H:%M:%S +0000 %Y"),
    )


def birthday_bots(users):
    """Return those created today, sorted oldest first"""
    selected = []

    # "May 09"
    nowstamp = time.strftime("%b %d", time.gmtime())  # UTC

    for user in users:
        if nowstamp in user["created_at"]:
            user["created_ts"] = created_at_timestamp(user)
            selected.append(user)

    # Sort oldest first
    selected = sorted(selected, key=lambda k: k["created_ts"])

    print("Birthday bots:")
    for user in selected:
        print(user["screen_name"], "\t", user["created_at"])

    return selected


def birthhour_bots(users):
    """Return those created this UTC hour"""
    selected = []

    "May 15 16:"
    hourstamp = time.strftime("%b %d %H:", time.gmtime())  # UTC

    print("Birthhour bots:")
    for user in users:
        if hourstamp in user["created_at"]:
            print(user["screen_name"], "\t", user["created_at"])
            selected.append(user)
    if not selected:
        print("None")

    return selected


def wish_a_happy_birthday(users):
    happy = random.choice(GREETS)
    p = inflect.engine()

    now_yyyy = int(time.strftime("%Y", time.gmtime()))

    for i, user in enumerate(users):
        yyyy = int(user["created_ts"][:4])
        years_old = now_yyyy - yyyy
        xth = p.ordinal(years_old)

        # Get an emoji per year
        if random.random() < 0.5:
            # All the same
            emoji = random.choice(EMOJI) * years_old
        else:
            emoji = "".join(random.sample(EMOJI, years_old))

        tweet = happy.format(xth, user["screen_name"], emoji)
        print_it(tweet)
        tweet_it(tweet)
        if i + 1 < len(users):  # if more to come
            time.sleep(15)


def tweet_it(string, in_reply_to_status_id=None):
    global TWITTER

    if len(string) <= 0:
        print("ERROR: trying to tweet an empty tweet!")
        return

    print_it("TWEETING THIS: " + string)

    if args.test:
        print("(Test mode, not actually tweeting)")
    else:
        print("POST statuses/update")
        result = TWITTER.statuses.update(
            status=string, in_reply_to_status_id=in_reply_to_status_id
        )
        url = (
            "http://twitter.com/"
            + result["user"]["screen_name"]
            + "/status/"
            + result["id_str"]
        )
        print("Tweeted: " + url)
        if not args.no_web:
            webbrowser.open(url, new=2)  # 2 = open in a new tab, if possible


if __name__ == "__main__":
    timestamp()

    parser = argparse.ArgumentParser(
        description="Tweet birthday wishes for bots created today",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-y",
        "--yaml",
        default="data/happy_botday.yaml",
        help="YAML file location containing Twitter keys and secrets",
    )
    parser.add_argument("-u", "--user", default="botally", help="The list owner")
    parser.add_argument("-l", "--list", default="omnibots", help="The list slug")
    parser.add_argument(
        "-nw",
        "--no-web",
        action="store_true",
        help="Don't open a web browser to show the tweeted tweet",
    )
    parser.add_argument(
        "-x",
        "--test",
        action="store_true",
        help="Test mode: go through the motions but don't tweet anything",
    )
    args = parser.parse_args()

    credentials = load_yaml(args.yaml)

    if TWITTER is None:
        TWITTER = Twitter(
            auth=OAuth(
                credentials["access_token"],
                credentials["access_token_secret"],
                credentials["consumer_key"],
                credentials["consumer_secret"],
            )
        )

    users = get_list_members(args.user, args.list)
    users = birthday_bots(users)
    users = birthhour_bots(users)  # Can comment this out for testing
    if users:
        wish_a_happy_birthday(users)


# End of file
