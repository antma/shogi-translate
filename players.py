# -*- coding: utf-8 -*-

import csv
import logging
import os
import pprint
import random
import requests
import time

def _cache_dir_create():
  if not os.path.lexists('.cache'):
    os.mkdir('.cache')

class PlayerBase:
  def __init__(self, base_filename, player_type):
    self._filename = base_filename
    self._player_type = player_type
    self._rows = []
    self._by_id = {}
  def add_player(self, player_id, jp_name, en_name):
    if player_id in self._by_id:
      return False
    self._by_id[player_id] = len(self._rows)
    self._rows.append((player_id, jp_name, en_name))
    return True
  def download_players(self, first, max_players, min_delay, max_delay):
    i = first
    session = requests.Session()
    while max_players > 0:
      p = Player(i, self._player_type)
      if p.dowload(session) > 0:
        delay = random.uniform(min_delay, max_delay)
        logging.debug(f"Sleeping for {delay} seconds.")
        time.sleep(delay)
      res = p.parse()
      if res < 0:
        logging.info(f"Can't parse player #{i}")
        break
      if res > 0:
        self.add_player(i, p.jp_name, p.en_name)
      else:
        logging.info(f"Empty english name for player #{i}")
      i += 1
      max_players -= 1
  def load(self):
    if not os.path.lexists(self._filename):
      return False
    with open(self._filename, 'r', newline='', encoding = 'utf-8') as csvfile:
      reader = csv.reader(csvfile, dialect = 'unix', quoting=csv.QUOTE_MINIMAL)
      header = next(reader)
      for player_id, jp_name, en_name in reader:
        self.add_player(player_id, jp_name, en_name)
    return True
  def save(self):
    with open(self._filename, 'w', newline='', encoding = 'utf-8') as csvfile:
      writer = csv.writer(csvfile, dialect = 'unix', quoting=csv.QUOTE_MINIMAL)
      writer.writerow(('id', 'jp_name', 'en_name'))
      for t in self._rows:
        writer.writerow(t)

class Player:
  def __init__(self, player_id, player_type = 'pro'):
    self.id = player_id
    assert((player_type == 'pro') or (player_type == 'lady'))
    self._type = player_type 
  def url(self):
    return f'https://www.shogi.or.jp/player/{self._type}/{self.id}.html'
  def filename(self):
    prefix = '' if self._type == 'pro' else 'l'
    return os.path.join('.cache', prefix + str(self.id) + '.html')
  def dowload(self, session = None):
    _cache_dir_create()
    output_filename = self.filename()
    if os.path.lexists(output_filename):
      logging.info(f'Player file "{output_filename}" is already downloaded')
      return 0
    url = self.url()
    logging.info(f'Downloading {url}')
    if session is None:
      r = requests.get(url)
    else:
      r = session.get(url)
    logging.debug(pprint.pformat(r.headers))
    logging.info(f'Request status code is {r.status_code}, encoding is {r.encoding}')
    if r.encoding != 'utf-8':
      logging.info('Changing encoding to "utf-8"')
      r.encoding = 'utf-8'
    if r.status_code == 200:
      with open(output_filename, 'w') as f:
        f.write(r.text)
      return 1
    return -1
  def parse(self):
    output_filename = self.filename()
    #if not os.path.lexists(output_filename):
    #  self.dowload()
    with open(output_filename, 'r') as f:
      state = 0
      for s in f:
        t = s.strip()
        if state == 0:
          if t.startswith('<h1 class="nameTtl">'):
            state = 1
        elif state == 1:
          pat = '<span class="jp">'
          i = t.index(pat)
          t = t[len(pat):]
          pat = '</span>'
          j = t.rindex(pat)
          self.jp_name = t[0:j].strip()
          state = 2
        elif state == 2:
          pat = '<span class="en">'
          i = t.index(pat)
          t = t[len(pat):]
          pat = '</span>'
          j = t.rindex(pat)
          self.en_name = t[0:j].strip()
          logging.debug(f'Player #{self.id}: {self.jp_name} -> {self.en_name}')
          if len(self.en_name) == 0: return 0
          return 1
    return -1
