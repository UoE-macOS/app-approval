#!/usr/bin/python
from jssapproval.jsstools import JSSTools 

j = JSSTools(config_file='/localdisk/macated/config.ini')

try:
  j.harvest()
except Exception as e:
  print e

