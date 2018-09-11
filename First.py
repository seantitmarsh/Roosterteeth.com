#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0105,C0325
'''
Created on Tue Aug 08 13:34:06 2017

@author: Sean.Titmarsh
'''

import sys
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')
#Some moron decided to use https://emojipedia.org/large-blue-circle/. This protects from that.
import praw
import sqlite3
import datetime
import pytz
import json
import urllib2

SITE = ['', '', '']
SUBREDDIT = ''
USERNAME = ''


def get_today():
    '''
    Get the date 90 days ago, used for url in get_surveys()

    Arguments
    None required

    Function Variables
    today -- Today's date
    offset -- Number of days to subtract from today's date (Default is 90)

    Returns
    date - String repersentation of date the date 90 days ago.
           Type: string (Format YYYY-MM-DD)
    '''
    central = pytz.timezone('US/Central')
    now = datetime.datetime.now(central) # timezone-aware datetime.utcnow()
    print(str(now) + '\r')
    today = datetime.datetime(now.year, now.month, now.day)
    return str(today)[:-9]


'''
Reddit Authentication
OAuth is now supported natively in PRAW, and this script uses the 'SCRIPT' flow at 
https://praw.readthedocs.io/en/latest/getting_started/authentication.html#oauth.

If you want to obsfucate account credentials, you can use Environment Variables or a praw.ini file
as described in https://praw.readthedocs.io/en/latest/getting_started/configuration/prawini.html.
'''

def reddit_oauth():
    '''
    Uses a praw.ini file in the working directory. Currently formatted as:

    [site_name]
    client_id=
    client_secret=
    password=
    username=
    user_agent=
    '''
    reddit = praw.Reddit('Main')
    return reddit

'''
REDDIT FUNCTIONS
Note, to work, pass reddit to each function. Otherwise, the praw instance won't be logged in.
'''
def submit_video(sub, name, link, reddit):
    '''
    Submit each YouTube feed entry and submit to Reddit.
    '''
    print('Now Submitting Video Thread for {1} to {0}'.format(sub, name) + '\r')
    submission = reddit.subreddit(sub).submit(title=name, url=link, resubmit='True', send_replies=False)
    return submission.id

def submit_comment(submissionId, name, episode, reddit):
    '''
    Submit each YouTube feed entry and submit to Reddit.
    '''
    print('Now Submitting Information Comment for {1} to {0}'.format(SUBREDDIT, name) + '\r')
    description = str(episode['attributes']['description'])
    process_description = description.split('\r\n\r\n')
    safe_description = process_description[0]
    esite = str(episode['attributes']['channel_slug'])
    eshow = str(episode['attributes']['show_title'])
    etitle = name
    ethumb = str(episode['included']['images'][0]['attributes']['large'])
    elength = get_time(episode['attributes']['length'])
    body = '|Title|' + etitle + '|  \r\n|-|-|  \r\n|Show|' + eshow + '|  \r\n|Site|' + esite + '|  \r\n|Thumbnail|[Link](' + ethumb + ')|  \r\n|Length|' + elength + '|  \r\n|Description|' + safe_description + '|'
    comment = reddit.submission(submissionId).reply(body)
    return comment.id

def get_time(length):
    '''
    Please don't look at this.
    '''
    hour = length/3600
    hour_sub = hour * 60
    minute = length/60
    second = length%60
    if hour >= 1:
        if minute <10:
            if second < 10:
                time = str(hour) + ':0' + str(minute - hour_sub) + ':0' + str(second)
            else:
                time = str(hour) + ':0' + str(minute - hour_sub) + ':' + str(second)
        else:
            if second < 10:
                time = str(hour) + ':' + str(minute - hour_sub) + ':0' + str(second)
            else:
                time = str(hour) + ':' + str(minute - hour_sub) + ':' + str(second)
    else:
        if second < 10:
            time = str(minute) + ':0' + str(second)
        else:
            time = str(minute) + ':' + str(second)
    print('Video Lengh: ' + time + '\r')
    return time

'''
ROOSTERTEETH.COM API FUNCTIONS
'''
def get_episodes():
    request = urllib2.Request('https://svod-be.roosterteeth.com/api/v1/episodes', headers={'User-Agent' : '')
    page = urllib2.urlopen(request).read()
    info = json.loads(page)
    return info['data']

def check_if_early(episode):
    first = episode['attributes']['sponsor_golive_at']
    public = episode['attributes']['public_golive_at']
    if first == public:
        return False
    else:
        return True

'''
EPISODE FUNCTIONS
Note, to work, pass reddit to each function. Otherwise, the praw instance won't be logged in.
'''

def check_videoId(videoId):
    '''

    '''
    conn = sqlite3.connect('First.db')
    c = conn.cursor()
    c.execute('SELECT * FROM Videos WHERE videoId = (?)', (videoId,))
    line = c.fetchone()
    if line == [] or line is None:
        match = 'New'
    else:
        match = 'Old'
    conn.close()
    return match

def save_videoId(title, submissionId, videoId, episode, today, reddit):
    '''

    '''
    conn = sqlite3.connect('First.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO Videos VALUES(?, ?, ?, ?, ?)', (title, submissionId, videoId, today, str(episode)))
    except:
        reddit.redditor(USERNAME).message('Video Save Failed', 'Video title: ' + title + ' submission failed.  \r\nVideo ID: ' + videoId + '  \r\nVideo Thread: https://reddit.com/' + submissionId + '  \r\nEpisode Info: ' + str(episode))
        try:
            c.execute('INSERT INTO Videos VALUES(?, ?, ?, ?, ?)', (str(title), submissionId, videoId, today, 'Exception, see messages'))
        except:
            c.execute('INSERT INTO Videos VALUES(?, ?, ?, ?, ?)', ('Exception, see messages', submissionId, videoId, today, 'Exception, see messages'))
    conn.commit()
    conn.close()




def run_bot():
    today = get_today()
    reddit = reddit_oauth()
    print('Logged in to Reddit\r')
    episodes = get_episodes()     # Obtain latest episode feed
    count = 0
    base_link = 'https://www.roosterteeth.com'
    while count <= 19:
        new_episode = episodes[count]
        count += 1    # Increment episode counter here, if something breaks it willl skip to the next episode
        #print(new_episode)   
        print('\r')
        print('Now running episode ' + str(count - 1) + '\r')
        e_title = str(new_episode['attributes']['title'])
        episode_title = e_title.replace("’", "'").replace('…', '...')
        print('Video Title: "' + episode_title + '"\r')
        video_site = str(new_episode['attributes']['channel_slug'])
        print('Site: ' + video_site + '\r')
        if video_site not in SITE:
            continue
        episode_id = str(new_episode['id'])
        print('Checking if video: "' + episode_title + '" and id: "' + episode_id + '" is new.\r')
        new = check_videoId(episode_id)
        if new == 'New':
            print('New video, starting submission checks:' + '\r')
            full_title = str(new_episode['attributes']['show_title']) + ': ' + episode_title
            episode_link = base_link + str(new_episode['canonical_links']['self'])
            first_only = str(new_episode['attributes']['is_sponsors_only'])
            first_early = str(check_if_early(new_episode))
            print('VIDEO INFORMATION:-------------------------------------------------\r')
            print('Full Title: ' + full_title + '\r')
            print('Episode ID: ' + episode_id + '\r')
            print('Episode Link: ' + episode_link + '\r')
            print('FIRST Exclusive?: ' + first_only + '\r')
            print('FIRST Early?: ' + first_early + '\r')
            if first_only == 'True' or first_early =='True':
                if first_only == 'True':
                    print('\rVideo is a First Exclusive Series, starting submission\r')
                elif first_early == 'True':
                    print('\rVideo is a First Early Series, starting submission\r')
                submissionId = str(submit_video(SUBREDDIT, full_title, episode_link, reddit))
                print('Reddit Thread ID: ' + submissionId + '\r')
                reddit.submission(submissionId).mod.approve()
                commentId = str(submit_comment(submissionId, full_title, new_episode, reddit))
                print('Reddit Comment ID: ' + commentId + '\r')
                reddit.comment(commentId).mod.approve()
                reddit.comment(commentId).mod.distinguish(how='yes', sticky=True)
                reddit.submission(submissionId).mod.flair(text='FIRST', css_class='first')
                save_videoId(full_title, submissionId, episode_id, new_episode, today, reddit)
            else:
                print('Ignore Release\r')
                save_videoId(full_title, 'Not Submitted', episode_id, new_episode, today, reddit)
        else:
            print('Old Video\r')
            new = False
        print('Finished video ' + str(count - 1) + '\r')


if __name__ == '__main__':

    try:
        run_bot()
    except SystemExit:
        print('Exit called.')
