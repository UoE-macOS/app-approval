import base64
import jss
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime


class Request(object):
    """ Class for handling individual application requests
        Requests are held as JSON blobs in the user objects of the JSS
    """

    def __init__(self, jsstools, uun, id):
        self.j = jsstools
        #TODO: Expand into instance variables?
        self.attributes = j.get_user_request(uun, id)

    def approve(self):
        self.attributes['status'] = 'Approved'
        self.attributes['actioned_at'] = datetime.now()
        #TODO: Update user group membership
        subject = "Request for {} approved".format(self.attributes['app'])
        msg = "Your request to install {} has been approved. It is now available to install through the JSS software catalogue".format(self.attributes['app'])
        self._contact_user(subject, msg)

    def deny(self):
        self.attributes['status'] = 'Denied'
        self.attributes['actioned_at'] = datetime.now()
        subject = "Request for {} denied".format(self.attributes['app'])
        msg = "Your request to install {} has been denied.".format(self.attributes['app'])
        self.contact_user(subject, msg)

    def contact_user(self, subject, message):
        them = self.attributes['uun'] + '@ed.ac.uk'
        us = 'donotreply@ed.ac.uk'
        m = MIMEText(message)
        m['Subject'] = subject
        m['From'] = us
        m['To'] = them

        s = smtplib.SMTP(localhost)
        s.send_message(m)
        s.quit


class JSSTools(object):
    """ Take a JSS object, run through looking for app requests and generate a
    list of requet objects
    """

    def __init__(self):
        prefs = jss.JSSPrefs()
        self.jss = jss.JSS(prefs)

    def _get_computer_reqs(self, computer_id):
        """ Get the requests from the computer object
        """
        comp = self.jss.Computer(computer_id)
        reqs = comp.find(".//extension_attribute[name='App Requests']/value").text.replace("\n","")
        #TODO: Get approvers based on hostname

        if reqs and (reqs != '\[  \]'):
            return self._b64_to_object(reqs)

    def get_all_computer_requests(self):
        """ Get a list of request objects from all computer objects in the JSS
        """
        requests = []
        computers = self.jss.Computer()
        for c in computers:
            r = self._get_computer_reqs('id')
            if r:
                requests.extend(r)
        return requests

    def get_user_request(self, uun, id):
        user = self._get_user_object(uun)
        reqs = self._b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text)
        match = []
        if reqs:
            match = [r for r in reqs if r['id'] == id]
        return match

    def add_user_request(self, uun, newreq):
        user = self._get_user_object(uun)
        reqs = self._b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text) or []
        reqs.append(newreq)
        user.find(".//extension_attribute[name='App Requests']/value").text = self._object_to_b64(reqs)
        user.save

    def _get_user_object(self, uun):
        return self.jss.User(uun)

    def _b64_to_object(self, blob):
        return json.loads(base64.b64decode(blob))

    def _object_to_b64(self, requests):
        return base64.b64encode(json.dumps(requests))

def harvest(j):
    computer_reqs = j.get_all_computer_reqs()
    for req in computer_reqs:
        if not j.get_user_request(req['uun'], req['id']):
            j.send_approval_link(req['uun'], req['id'])
            j.add_user_request(req['uun'], req)

if __name__ == '__main__':
    j = JSSTools()
    harvest(j)
