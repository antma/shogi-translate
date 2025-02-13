# -*- coding: utf-8 -*-

#standard
import logging
import os
import pprint
import random
import time

#library
import requests

#project
import csv_unix
import utils

class PlayerBase:
  def __init__(self, base_filename, player_type):
    self._filename = base_filename
    self._player_type = player_type
    self._rows = []
    self._by_id = {}
  def add_player(self, player_id, jp_name, en_name):
    if isinstance(player_id, str):
      player_id = int(player_id)
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
    for (player_id, jp_name, en_name) in csv_unix.words_load(self._filename):
      self.add_player(player_id, jp_name, en_name)
  def save(self):
    csv_unix.words_save(self._filename, self._rows)

class Player:
  def __init__(self, player_id, player_type = 'pro'):
    self.id = player_id
    assert((player_type == 'pro') or (player_type == 'lady'))
    self._type = player_type
    self.jp_name = None
    self.en_name = None
  def url(self):
    return f'https://www.shogi.or.jp/player/{self._type}/{self.id}.html'
  def filename(self):
    prefix = '' if self._type == 'pro' else 'l'
    return utils.cache_filename(prefix + str(self.id) + '.html')
  def dowload(self, session = None):
    utils.cache_dir_create()
    output_filename = self.filename()
    if os.path.lexists(output_filename):
      logging.info(f'Player file "{output_filename}" is already downloaded')
      return 0
    url = self.url()
    logging.info(f'Downloading {url}')
    if session is None:
      r = requests.get(url, timeout = 10.0)
    else:
      r = session.get(url, timeout = 10.0)
    logging.debug(pprint.pformat(r.headers))
    logging.info(f'Request status code is {r.status_code}, encoding is {r.encoding}')
    if r.encoding != 'utf-8':
      logging.info('Changing encoding to "utf-8"')
      r.encoding = 'utf-8'
    if r.status_code == 200:
      with open(output_filename, 'w', encoding = 'utf-8') as f:
        f.write(r.text)
      return 1
    return -1
  def parse(self):
    output_filename = self.filename()
    #if not os.path.lexists(output_filename):
    #  self.dowload()
    with open(output_filename, 'r', encoding = 'utf-8') as f:
      state = 0
      for s in f:
        t = s.strip()
        if state == 0:
          if t.startswith('<h1 class="nameTtl">'):
            state = 1
        elif state == 1:
          pat = '<span class="jp">'
          i = t.index(pat)
          t = t[i+len(pat):]
          pat = '</span>'
          j = t.rindex(pat)
          self.jp_name = t[0:j].strip()
          state = 2
        elif state == 2:
          pat = '<span class="en">'
          i = t.index(pat)
          t = t[i + len(pat):]
          pat = '</span>'
          j = t.rindex(pat)
          self.en_name = t[0:j].strip()
          logging.debug(f'Player #{self.id}: {self.jp_name} -> {self.en_name}')
          if len(self.en_name) == 0:
            return 0
          return 1
    return -1
