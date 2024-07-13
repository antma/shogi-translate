# -*- coding: utf-8 -*-
""" loading/saving dictionaries in CSV format """

import csv
import os

def words_load(filename):
  if not os.path.lexists(filename):
    return []
  with open(filename, 'r', newline='', encoding = 'utf-8') as csvfile:
    reader = csv.reader(csvfile, dialect = 'unix', quoting=csv.QUOTE_MINIMAL)
    #skip header
    next(reader)
    return list(reader)

def words_save(filename, rows):
  with open(filename, 'w', newline='', encoding = 'utf-8') as csvfile:
    writer = csv.writer(csvfile, dialect = 'unix', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(('id', 'jp_name', 'en_name'))
    for t in rows:
      writer.writerow(t)
