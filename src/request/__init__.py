import base64
import jss
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from xml.etree import ElementTree


class Request(object):
    """ Class for handling individual application requests
        Requests are held as JSON blobs in the user objects of the JSS
    """

    def __init__(self, UUID, uun=None):
        self.j = JSSTools()

        if uun:
            self.attributes = self.j.get_user_request(uun, UUID)[0]
            self.user = self.j.get_user_object(uun)
        else:
            self.attributes = self.j.get_user_requests_all(UUID)[0]
            self.user = self.j.get_user_object(self.attributes['UUN'])

	if 'status' not in self.attributes:
	    self.attributes['status'] = 'Pending'

    def approve(self):
        if self.attributes['status'] != 'Pending':
            raise ValueError("Request already handled: "+self.attributes['status'])
        if 'policy' not in self.attributes:
            self.attributes['policy'] = "Unknown application"
        self.attributes['status'] = 'Approved'
        self.attributes['actioned_at'] = datetime.now().isoformat()

	self.j.approve(self.user, self.attributes['policy'])

        subject = "Request for {} approved".format(self.attributes['policy'])
        msg = "Your request to install {} has been approved. It is now available to install through the JSS software catalogue".format(self.attributes['policy'])
        self.j.contact_user(self.user, subject, msg)

	self.j.update_user_request(self.user, self.attributes)

    def update(self):
	self.j.update_user_request(self.user, self.attributes)

    def deny(self):
        if self.attributes['status'] != 'Pending':
            raise ValueError("Request already handled: "+self.attributes['status'])
        if 'policy' not in self.attributes:
            self.attributes['policy'] = "Unknown application"
        self.attributes['status'] = 'Denied'
        self.attributes['actioned_at'] = datetime.now().isoformat()
        subject = "Request for {} denied".format(self.attributes['policy'])
        msg = "Your request to install {} has been denied.".format(self.attributes['policy'])
        self.j.contact_user(self.user, subject, msg)

	self.j.update_user_request(self.user, self.attributes)


class Approvers(object):
    """ Wrapper for getting & returning approvers
    """

    def __init__(self):

        # Right now, expecting a text file that contains a JSON
        # dict, with a list of approvers by each key e.g.
        # {'S48': 'seesup@ed.ac.uk',
        #  'ENG': 'seesup@ed.ac.uk'}
        with open('/localdisk/macated/approvers.txt', 'r') as f:
            self.approvers = json.load(f)

    def get_approver(self, host):
        if host[-8:] == 'ed.ac.uk':
            area = host.split('.')[-4].upper()
        elif '-' in host:
            area = host.split('-')[0].upper()
        else:
            #raise ValueError("Machine name has no area identifier")
            return ''

        return self.approvers[area]

class JSSTools(object):
    """ Take a JSS object, run through looking for app requests and generate a
    list of requet objects
    """

    def __init__(self, debug=False):
        prefs = jss.JSSPrefs()
        self.jss = jss.JSS(prefs)
        self.approvers = Approvers()
	self.debug = debug

    def approve(self, user, policy):
	xml = "<user_group><user_additions><user><id>{}</id></user></user_additions></user_group>".format(user.id)
	put_object = ElementTree.fromstring(xml)
        usergroup = self.get_usergroup(policy)
	
	self.jss.put('/usergroups/id/{}'.format(usergroup),
	      put_object)

    def _get_computer_reqs(self, computer_id):
        """ Get the requests from the computer object
        """
        comp = self.jss.Computer(computer_id)
        reqs = comp.find(".//extension_attribute[name='App Requests']/value").text.replace("\n","")
        req_list = []
        if (reqs != 'None'):
            req_list = self._b64_to_object(reqs)
            for r in req_list:
                r['host'] = comp.find('.//name').text
                r['approver'] = self.approvers.get_approver(r['host'])
                r['status'] = "Pending"
	return req_list

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

    def get_usergroup(self, policy):
	groupname = "approved_"+policy
	group = self.jss.UserGroup(groupname)
	return group.id	

    def get_user_request(self, uun, UUID):
        user = self.get_user_object(uun)
        reqs = self._b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text)
        match = []
        if reqs:
            match = [r for r in reqs if r['UUID'] == UUID]
        return match

    def get_user_requests_uun(self, uun):
        user = self.get_user_object(uun)
        reqs = self._b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text)
        return reqs

    def get_user_requests_all(self, UUID):
        users = self.jss.User()
        req_list = []
        for u in users:
            uo = self.jss.User(u['id'])
            reqs = self._b64_to_object(uo.find(".//extension_attribute[name='App Requests']/value").text)
            if reqs:
                req_list.extend([r for r in reqs if r['UUID'] == UUID])
	return req_list

    def add_user_request(self, uun, newreq):
        user = self.get_user_object(uun)
        reqs = self._b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text) or []
        reqs.append(newreq)
        user.find(".//extension_attribute[name='App Requests']/value").text = self._object_to_b64(reqs)
        user.save

    def update_user_request(self, user, newreq):
        reqs = self._b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text)
        if not reqs:
            raise ValueError("User has no requests to update")
        updated = [r for r in reqs if r['UUID'] != newreq['UUID']]
        updated.append(newreq)
        user.find(".//extension_attribute[name='App Requests']/value").text = self._object_to_b64(updated)
        user.save()

    def get_user_object(self, uun):
        return self.jss.User(uun)

    def contact_user(self, user, subject, message):
        them = user.find('.//email').text
        us = 'donotreply@ed.ac.uk'
        m = MIMEText(message)
        m['Subject'] = subject
        m['From'] = us
        m['To'] = them

	if self.debug:
            print m
	else:
            s = smtplib.SMTP(localhost)
            s.send_message(m)
            s.quit

    def _b64_to_object(self, blob):
	if blob is not None:
	    return json.loads(base64.b64decode(blob))
        return []

    def _object_to_b64(self, requests):
        return base64.b64encode(json.dumps(requests))

    def harvest(self):
        computer_reqs = self.get_all_computer_reqs()
        for req in computer_reqs:
            if not self.get_user_request(req['uun'], req['UUID']):
                self.add_user_request(req['uun'], req)

