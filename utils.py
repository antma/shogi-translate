# -*- coding: utf-8 -*-
""" logging setup """

import logging
import os
import sys

CACHE_DIR = '.cache'

def init_logging(log_filename, logging_level = logging.INFO):
  fmt = '%(asctime)s %(levelname)s [%(module)s] %(message)s'
  if log_filename is None:
    logging.basicConfig(level=logging_level, format=fmt, stream=sys.stdout)
  else:
    logging.basicConfig(level=logging_level, format=fmt, filename=log_filename, filemode='w')

def cache_dir_create():
  if not os.path.lexists(CACHE_DIR):
    os.mkdir(CACHE_DIR)

def cache_filename(base_filename):
  return os.path.join(CACHE_DIR, base_filename)
