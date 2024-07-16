# -*- coding: utf-8 -*-
""" download youtube playlist, google translate """

#standard
import logging
import os
import pickle
import subprocess
import csv

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
    self._updates.append((text, t))
    self._cache[text] = t
    return t

def _google_translate(text):
  """ use Google Translate via translate-shell package """
  cmd = ['trans', '-b', '-e', 'google', 'ja:en', text]
  logging.debug(f'Run command: {cmd}')
  r = subprocess.run(cmd, check = False, shell = False, capture_output=True)
  if r.returncode != 0:
    logging.warning(f"trans exit code {r.returncode}")
    logging.debug('%s', r.stderr.decode('utf-8'))
    return None
  return r.stdout.decode('utf-8')
