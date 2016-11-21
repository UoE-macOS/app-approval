#!/usr/bin/python

# PoC middleware code for managing application
# requests via computer and user extension attributes
# in the JSS

# The required JSS module can be found here: 
# https://github.com/sheagcraig/python-jss

import jss
import json
import base64

# Ugh - globals!
jss_prefs = jss.JSSPrefs()
j = jss.JSS(jss_prefs)

def get_computer_reqs(computer_id):
  """ Get all requests from the 'App Requests' 
      extension attribute of an individual
      computer object """
  c = j.Computer(computer_id)
  # Should be a base64 encoded blob of JSON
  reqs = c.find(".//extension_attribute[name='App Requests']/value").text.replace("\n","")
  if reqs != "None" and reqs != "\[  \]":
    print "Found request on computer id %s" % computer_id
    return b64_to_object(reqs)
  else:
    return None

def get_all_computer_reqs():
  """ Loop through all computer objects, building
      a list of request dictionaries """
  print "Checking all computer objects for requests..."
  all_reqs = []
  all_comps = j.Computer()
  for c in all_comps:
    new_reqs = get_computer_reqs(c['id'])
    if new_reqs is not None:
      all_reqs = all_reqs + new_reqs
  return all_reqs

def get_request_from_user_object(user, id):
  """ If a request with id 'id' exists in the
      App Requests extension attribute of 'user',
      return it in object form """
  print "Checking user object %s for request %s" % (user.name, id)
  reqs = b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text)
  if reqs is not None:
    match = [ r for r in reqs if r['id'] == id ] 
    if len(match) > 0:
      print "Found it!"
      return match
    else:
      print "Not found"

def add_request_to_user_object(user, newreq):
  """ Add 'newreq' to the App Requests extension
      attribute of the user object 'user' """
  print "Adding request id %s to user %s" % (newreq['id'], user.name)

  # We're going append this request to any that exist already in the user object
  # so retrive the current value of the attribute...
  reqs = b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text)
  if reqs == None: reqs = [] 
  reqs = reqs + [ newreq ]
  user.find(".//extension_attribute[name='App Requests']/value").text = object_to_b64(reqs)
  
  user.save()

def b64_to_object(blob):
  if blob is not None:
    return json.loads(base64.b64decode(blob))

def object_to_b64(obj):
  if obj is not None:
    return base64.b64encode(json.dumps(obj))

def get_user_object(uun):
  return j.User(uun)

def send_email(uun):
  print "Sending email to %s" % uun

if __name__ == '__main__':
  all_reqs = get_all_computer_reqs()

  for req in all_reqs:
    if get_request_from_user_object(get_user_object(req['uun']), req['id']) is None:
      send_email(req['uun'])
      add_request_to_user_object(get_user_object(req['uun']), req)
    else:
      pass

  print "Done"

