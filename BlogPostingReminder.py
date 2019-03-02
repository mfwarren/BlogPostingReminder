#!/usr/bin/env python
# written by Matt Warren
# https://mattwarren.co/

import datetime
import json
import os

import feedparser
from croniter import croniter
from twx.botapi import TelegramBot
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import dateutil.parser
import pytz

LOCAL = os.path.dirname(os.path.realpath(__file__))

try:
    with open(os.path.join(LOCAL, 'schedule.json')) as json_file:
        SETTINGS = json.load(json_file)
except FileNotFoundError:
    print('Missing schedule.json config file')
    raise

TELEGRAM_BOT_APIKEY = os.environ['TELEGRAM_BOT_APIKEY']
TELEGRAM_USER_ID = int(os.environ['TELEGRAM_USER_ID'])

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

bot = TelegramBot(TELEGRAM_BOT_APIKEY)
bot.update_bot_info().wait()

today = datetime.datetime.utcnow()
today_tz = today.replace(tzinfo=pytz.utc)


def check_blog(blog):
    print(f"checking {blog['name']}")
    d = feedparser.parse(blog['url'])
    lastPost = d.entries[0]

    if 'modified_parsed' in lastPost.keys():
        date_parsed = lastPost.modified_parsed
    elif 'published_parsed' in lastPost.keys():
        date_parsed = lastPost.published_parsed

    pubDate = datetime.datetime(
        date_parsed[0],
        date_parsed[1],
        date_parsed[2],
        date_parsed[3],
        date_parsed[4],
        date_parsed[5],
    )

    iter = croniter(blog['schedule'], pubDate)
    next_post_expected_at = iter.get_next(datetime.datetime)

    if next_post_expected_at < today:
        msg = f"{blog['name']} needs attention! last post {str((today-pubDate).days)} days ago."
        print(msg)
        bot.send_message(TELEGRAM_USER_ID, msg).wait()
    else:
        msg = f"{blog['name']} is fresh! last post {str((today-pubDate).days)} days ago."
        print(msg)


def check_gdrive(blog):
    file2 = drive.CreateFile({'id': blog['gdrive-id']})
    file2.FetchMetadata(fields='modifiedByMeDate')
    pubDate = dateutil.parser.parse(file2['modifiedByMeDate'])

    iter = croniter(blog['schedule'], pubDate)
    next_post_expected_at = iter.get_next(datetime.datetime)

    if next_post_expected_at < today_tz:
        msg = f"{blog['name']} needs attention! last updated {str((today_tz-pubDate).days)} days ago."
        print(msg)
        bot.send_message(TELEGRAM_USER_ID, msg).wait()
    else:
        msg = f"{blog['name']} is fresh! last updated {str((today_tz-pubDate).days)} days ago."
        print(msg)


if __name__ == '__main__':
    for blog in SETTINGS:
        if 'gdrive-id' in blog:
            check_gdrive(blog)
        else:
            check_blog(blog)
