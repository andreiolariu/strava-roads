import cookielib
import time
import urllib
import urllib2
import re

from BeautifulSoup import BeautifulSoup
import numpy as np
import simplejson as json

TIME_BT_REQUESTS = 2


def fetch_url(url):
  try:
    print 'fetching %s' % url
    response = opener.open(url)
    time.sleep(TIME_BT_REQUESTS)
  except Exception, e:
    print '%s - %s' % (e, url)
    time.sleep(TIME_BT_REQUESTS)
    return None

  if response.getcode() != 200:
    raise Exception('%s: %s - %s' % \
        (url, response.getcode(), response.msg))

  response = response.read()
  return response


# authentication code by: https://github.com/loisaidasam/stravalib
def log_in():
  print "Logging in..."
  cj = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

  f = opener.open('https://www.strava.com/login')
  soup = BeautifulSoup(f.read())

  time.sleep(TIME_BT_REQUESTS)

  utf8 = soup.findAll('input', {'name': 'utf8'})[0].get('value').encode('utf-8')
  token = soup.findAll('input', {'name': 'authenticity_token'})[0].get('value')

  values = {
    'utf8': utf8,
    'authenticity_token': token,
    'email': '<< your email here >>',
    'password': '<< your password here >>',
  }

  data = urllib.urlencode(values)
  url = 'https://www.strava.com/session'
  response = opener.open(url, data)
  soup = BeautifulSoup(response.read())

  time.sleep(TIME_BT_REQUESTS)
  return opener


athlete_rides = {}
ride_data = {}

def get_athlete_info(opener, athlete_id):
  # without these headers, the request doesn't return anything
  opener.addheaders = [
    ('X-Requested-With', 'XMLHttpRequest'),
    ('Accept', 
      ('text/javascript, application/javascript, application/ecmascript,'
      ' application/x-ecmascript')
    ),
  ]

  if athlete_id not in athlete_rides:
    rides = []
    for interval in ['201606', '201605', '201604']:
      url = 'https://www.strava.com/athletes/%s/interval?interval=%s&interval_type=month&chart_type=miles&year_offset=0' \
          % (athlete_id, interval)
      
      response = fetch_url(url)
      if not response:
        continue
      response = response.replace(' rode with ', '|separator|')
      response = response.replace('app-icon icon-ride icon-sm type', '|separator|')

      rides_batch = response.split('|separator|')[1:]
      rides_batch = [r.split('/activities/')[1].split('\\')[0] for r in rides_batch]
      rides.extend(rides_batch)

    athlete_rides[athlete_id] = rides

  for ride in athlete_rides[athlete_id]:
    if ride not in ride_data:
      url = 'https://www.strava.com/activities/%s/streams' % ride
      response = fetch_url(url)
      if response:
        response = json.loads(response)
      else:
        response = None

      f = open('ride_data.json', 'a')
      f.write(json.dumps((ride, response)))
      f.write('\n')

      ride_data[ride] = 1

def get_athletes(club_id):
  page = 1
  member_ids = []
  while True:
    url = 'https://www.strava.com/clubs/%s/members?page=%s' % (club_id, page)
    response = fetch_url(url)
    matches = re.findall('\/athletes\/\d+', response)
    member_ids.extend([m.split('/')[2] for m in matches])

    if len(matches) < 100:
      break
    page += 1

  return member_ids


def save_data():
  data = json.dumps(athletes)
  f = open('athletes.json', 'w')
  f.write(data)
  f.close()

  data = json.dumps(athlete_rides)
  f = open('athlete_rides.json', 'w')
  f.write(data)
  f.close()


def load_cache():
  athletes = json.loads(open('athletes.json', 'r').read())
  athlete_rides = json.loads(open('athlete_rides.json', 'r').read())
  ride_data = {}
  f = open('ride_data.json', 'r')
  while True:
    row = f.readline()
    if not row:
      break
    ride_id = row.split('", ')[0][2:]
    ride_data[ride_id] = 1


def get_data():
  opener = log_in()

  clubs = ['38078', '37183', '186539', '126088', '26378', '15443', '35212', '24175', '53666']

  athletes = []
  for club_id in clubs:
    athletes.extend(get_athletes(club_id))

  athletes = list(set(athletes))

  for athlete in athletes:
    get_athlete_info(opener, athlete)


get_data()
