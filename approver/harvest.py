import apprequest

j = apprequest.JSSTools(config_file='/localdisk/macated/config.ini')

try:
  j.harvest()
except Exception as e:
  print e

