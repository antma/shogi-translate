# -*- coding: utf-8 -*-
""" download youtube playlist, google translate """

#standard
import random
import logging
import os
import pprint
import subprocess
import csv
import time
from datetime import datetime

#library
import feedparser
import PyRSS2Gen

#project
import utils

def youtube_recent_videos(channel_url, limit = 10, days = 3):
  cols = ['duration_string', 'id', 'view_count']
  str_cols = ' '.join(map(lambda x: '%(' + x + ')s', cols))
  cmd = ['yt-dlp', '--verbose', '--flat-playlist', '--playlist-end', str(limit), '--dateafter', f'now-{days}day', '--print', 'title', '--print', str_cols, channel_url + '/videos']
  logging.debug(f'Run command: {cmd}')
  r = subprocess.run(cmd, check = False, shell = False, capture_output=True)
  if r.returncode != 0:
    logging.warning(f"yt-dlp exit code {r.returncode}")
    logging.debug('%s', r.stderr.decode('utf-8'))
    return None
  d = {}
  res = []
  for (i, s) in enumerate(r.stdout.decode('utf-8').split('\n')):
    if i % 2 == 0:
      d['title'] = s
    else:
      a = list(s.split())
      for key, value in zip(cols, a, strict=True):
        d[key] = value
      res.append(d)
      d = {}
  return res

class CachedCSVGoogleTranslate:
  """ should be used by with statement """
  def __init__(self):
    self._cache = {}
    self._cache_filename = utils.cache_filename('cached_google_translate.csv')
    self._updates = []
    if os.path.lexists(self._cache_filename):
      with open(self._cache_filename, 'r', encoding = 'utf-8') as csvfile:
        reader = csv.reader(csvfile, dialect = 'unix', quoting=csv.QUOTE_MINIMAL)
        for jp, en in reader:
          if en == '':
            logging.debug('Skip empty translation')
          else:
            self._cache[jp] = en
  def __enter__(self):
    return self
  def __exit__(self, exc_type, exc_value, traceback):
    if len(self._updates) > 0:
      with open(self._cache_filename, 'a', encoding = 'utf-8') as csvfile:
        writer = csv.writer(csvfile, dialect = 'unix', quoting=csv.QUOTE_MINIMAL)
        for t in self._updates:
          writer.writerow(t)
  def translate(self, text):
    p = self._cache.get(text)
    if p != None: return p
    t = _google_translate(text)
    if t is None:
      return None
    self._updates.append((text, t))
    self._cache[text] = t
    return t
  def shogidb2_translate_games(self, output_rss_filename):
    rss_url = 'https://shogidb2.com/rss'
    d = feedparser.parse(rss_url)
    logging.debug(pprint.pformat(d))
    items = []
    f = d['feed']
    feed_title = self.translate(f['title'])
    for e in d['entries']:
      link = e['link']
      if not link.startswith('https://shogidb2.com/games/'): continue
      summary = self.translate(e['summary'])
      title = self.translate(e['title'])
      items.append(PyRSS2Gen.RSSItem(
        title = title,
        description = summary,
        link = link,
        guid = PyRSS2Gen.Guid(link),
        pubDate = _cvt_date(e['published_parsed'])
      ))
    rss = PyRSS2Gen.RSS2(title = feed_title, description = '', link = f['link'], items = items)
    with open(output_rss_filename, "w") as g:
      rss.write_xml(g)
  def youtube_translate_video_playlist(self, channel, output_rss_filename, filter_title = None):
    rss_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel}'
    d = feedparser.parse(rss_url)
    logging.debug(pprint.pformat(d))
    items = []
    f = d['feed']
    feed_title = self.translate(f['title'])
    for e in d['entries']:
      title = e['title']
      views = int(e['media_statistics']['views'])
      if views == 0: continue
      if (not filter_title is None) and (not filter_title(title)): continue
      title = self.translate(title)
      link = e['link']
      items.append(PyRSS2Gen.RSSItem(
        title = title,
        description = f'views: {views}',
        link = link,
        guid = PyRSS2Gen.Guid(link),
        pubDate = _cvt_date(e['published_parsed'])
      ))
    rss = PyRSS2Gen.RSS2(title = feed_title, description = '', link = f['link'], items = items, pubDate = _cvt_date(f['published_parsed']))
    with open(output_rss_filename, "w") as g:
      rss.write_xml(g)
  def jsa_atom(self, output_rss_filename):
    atom_url = 'https://www.shogi.or.jp/atom.xml'
    d = feedparser.parse(atom_url)
    logging.debug(pprint.pformat(d))
    items = []
    f = d['feed']
    feed_title = self.translate(f['title'])
    for e in d['entries']:
      link = e['link']
      #if not link.startswith('https://shogidb2.com/games/'): continue
      summary = self.translate(e['summary'])
      title = self.translate(e['title'])
      items.append(PyRSS2Gen.RSSItem(
        title = title,
        description = summary,
        link = link,
        guid = PyRSS2Gen.Guid(link),
        pubDate = _cvt_date(e['published_parsed'])
      ))
    rss = PyRSS2Gen.RSS2(title = feed_title, description = '', link = f['link'], items = items)
    with open(output_rss_filename, "w") as g:
      rss.write_xml(g)
def _google_translate(text):
  """ use Google Translate via translate-shell package """
  cmd = ['trans', '-b', '-e', 'google', 'ja:en', text]
  logging.debug(f'Run command: {cmd}')
  r = subprocess.run(cmd, check = False, shell = False, capture_output=True)
  time.sleep(random.uniform(0.5, 1.5))
  if r.returncode != 0:
    logging.warning(f"trans exit code {r.returncode}")
    logging.debug('%s', r.stderr.decode('utf-8'))
    return None
  res = r.stdout.decode('utf-8')
  logging.debug(res)
  return res

def _cvt_date(s):
  return datetime.fromtimestamp(time.mktime(s))

