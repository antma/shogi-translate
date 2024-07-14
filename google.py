# -*- coding: utf-8 -*-
""" download youtube playlist, google translate """

#standard
import logging
import os
import pickle
import subprocess

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

class CachedGoogleTranslate:
  """ should be used by with statement """
  def __init__(self):
    self._cache = {}
    self._cache_filename = utils.cache_filename('cached_google_translate.pickle')
    if os.path.lexists(self._cache_filename):
      with open(self._cache_filename, 'rb') as f:
        self._cache = pickle.load(f)
    self._pickle_len = len(self._cache)
  def __enter__(self):
    return self
  def __exit__(self, exc_type, exc_value, traceback):
    l = len(self._cache)
    if l > self._pickle_len:
      logging.info(f"Saving google translate cache ({l} items)")
      with open(self._cache_filename, 'wb') as f:
        self._cache = pickle.dump(self._cache, f, protocol = pickle.HIGHEST_PROTOCOL)
  def translate(self, text):
    p = self._cache.get(text)
    if p != None: return p
    t = _google_translate(text)
    self._cache[text] = t
    return t

def _google_translate(text):
  """ use Google Translate via translate-shell package """
  cmd = ['trans', '-b', '-e google', 'ja:en', text]
  logging.debug(f'Run command: {cmd}')
  r = subprocess.run(cmd, check = False, shell = False, capture_output=True)
  if r.returncode != 0:
    logging.warning(f"trans exit code {r.returncode}")
    logging.debug('%s', r.stderr.decode('utf-8'))
    return None
  return r.stdout.decode('utf-8')
  



  
