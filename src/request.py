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

    def __init__(self, jsstools, uun, UUID):
        self.j = jsstools
        self.attributes = j.get_user_request(uun, UUID)
        self.user = j.get_user_object(uun)

    def approve(self):
        self.attributes['status'] = 'Approved'
        self.attributes['actioned_at'] = datetime.now()

        usergroup = "approved_"+self.attributes['policy']

        subject = "Request for {} approved".format(self.attributes['policy'])
        msg = "Your request to install {} has been approved. It is now available to install through the JSS software catalogue".format(self.attributes['policy'])
        j.contact_user(self.user, subject, msg)

    def deny(self):
        self.attributes['status'] = 'Denied'
        self.attributes['actioned_at'] = datetime.now()
        subject = "Request for {} denied".format(self.attributes['policy'])
        msg = "Your request to install {} has been denied.".format(self.attributes['policy'])
        j.contact_user(user, subject, msg)


class Approvers(object):
    """ Wrapper for getting & returning approvers
    """

    def __init__(self):

        # Right now, expecting a text file that contains a JSON
        # dict, with a list of approvers by each key e.g.
        # {'S48': 'seesup@ed.ac.uk',
        #  'ENG': 'seesup@ed.ac.uk'}
        with open('/localdisk/macated/approvers', 'r') as f:
            self.approvers = json.load(f)

    def get_approver(self, host):
        if host[-9:] == 'ed.ac.uk':
            area = host.split('.')[-4].upper()
        elif '-' in host:
            area = host.split('-')[0].upper()
        else:
            raise ValueError("Machine name has no area identifier")

        return self.approvers[area]

class JSSTools(object):
    """ Take a JSS object, run through looking for app requests and generate a
    list of requet objects
    """

    def __init__(self):
        prefs = jss.JSSPrefs()
        self.jss = jss.JSS(prefs)
        self.approvers = Approvers()

    def _get_computer_reqs(self, computer_id):
        """ Get the requests from the computer object
        """
        comp = self.jss.Computer(computer_id)
        reqs = comp.find(".//extension_attribute[name='App Requests']/value").text.replace("\n","")
        if reqs:
            req_list = self._b64_to_object(reqs)
            for r in req_list:
                r['host'] = comp.find('.//name')
                r['approver'] = self.approvers.get_approver(r['host'])
                r['status'] = "Pending"

    def get_all_computer_requests(self):
        """ Get a list of request objects from all computer objects in the JSS
        """
        requests = []
        computers = self.jss.Computer()
        for c in computers:
            r = self._get_computer_reqs(c['id'])
            if r:
                requests.extend(r)
        return requests

    def get_user_request(self, uun, UUID):
        user = self.get_user_object(uun)
        reqs = self._b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text)
        match = []
        if reqs:
            match = [r for r in reqs if r['UUID'] == UUID]
        return match

    def add_user_request(self, uun, newreq):
        user = self.get_user_object(uun)
        reqs = self._b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text) or []
        reqs.append(newreq)
        user.find(".//extension_attribute[name='App Requests']/value").text = self._object_to_b64(reqs)
        user.save

    def get_user_object(self, uun):
        return self.jss.User(uun)

    def contact_user(self, user, subject, message):
        them = user.find('.//email')
        us = 'donotreply@ed.ac.uk'
        m = MIMEText(message)
        m['Subject'] = subject
        m['From'] = us
        m['To'] = them

        s = smtplib.SMTP(localhost)
        s.send_message(m)
        s.quit

    def _b64_to_object(self, blob):
        return json.loads(base64.b64decode(blob))

    def _object_to_b64(self, requests):
        return base64.b64encode(json.dumps(requests))


def harvest(j):
    computer_reqs = j.get_all_computer_reqs()
    for req in computer_reqs:
        if not j.get_user_request(req['uun'], req['UUID']):
            j.add_user_request(req['uun'], req)

if __name__ == '__main__':
    j = JSSTools()
    harvest(j)
