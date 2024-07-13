# -*- coding: utf-8 -*-
""" module for loading wordbook and translation strings """

from collections import defaultdict
import logging

import csv_unix

class WordBook:
  def __init__(self):
    self._d = defaultdict(list)
    self._s = set()
  def _load(self, filename):
    n = 0
    for (line, (_, jp_name, en_name)) in enumerate(csv_unix.words_load(filename)):
      if jp_name in self._s:
        logging.warning(f'Found duplicate translation in file "{filename}" at line {line+1}')
        continue
      self._s.add(jp_name)
      c = jp_name[0]
      self._d[c].append((jp_name, en_name))
      n += 1
    logging.info(f'Add {n} words from filename "{filename}"')
  def load_all(self):
    for tp in ['pro', 'lady', 'title', 'openings', 'other']:
      self._load(tp + '.csv')
  def _match(self, s, pos):
    p = self._d.get(s[pos])
    if p is None:
      return None
    for (jp_name, en_name) in p:
      if s.startswith(jp_name, pos):
        return (jp_name, en_name)
    return None
  def translate(self, s):
    t = ''
    i = 0
    l = len(s)
    while i < l:
      p = self._match(s, i)
      if p is None:
        t += s[i]
        i += 1
      else:
        (jp_name, en_name) = p
        t += ' ' + en_name + ' '
        i += len(jp_name)
    return t
