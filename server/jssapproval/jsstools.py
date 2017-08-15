import base64
import jss
import json
import smtplib
from ConfigParser import ConfigParser
from datetime import datetime
from xml.etree import ElementTree
from approvers import Approvers


class JSSTools(object):
    """ Take a JSS object, run through looking for app requests and generate a
    list of requet objects
    """

    def __init__(self, config_file='/etc/jssapproval/config.ini', debug=False):
        config = ConfigParser()
        config.read(config_file)

        # JSS config
        jss_url = config.get('jss', 'jss_url')
        jss_user = config.get('jss', 'jss_user')
        if config.get('jss', 'jss_password_type') == 'FILE':
            with open(config.get('jss', 'jss_pass'), 'r') as f:
                jss_password = f.read().strip()
        else:
            jss_password = config.get('jss', 'jss_pass')
        self.jss = jss.JSS(url=jss_url,
                           user=jss_user,
                           password=jss_password)

        # Approvers config
        approver_url = config.get('approvers', 'approver_url')
        approver_user = config.get('approvers', 'approver_user')
        if config.get('approvers', 'approver_password_type') == 'FILE':
            with open(config.get('approver', 'approver_pass'), 'r') as f:
                approver_password = f.read().strip()
        else:
            approver_password = config.get('approver', 'approver_pass')
        self.approvers = Approvers(url=approver_url,
                                   user=approver_user,
                                   password=approver_password)
        
        self.templates = config.get('templates', 'template_location')
        self.base_url = config.get('service', 'base_url')

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
        try:
            reqs = comp.find(".//extension_attribute[name='App Requests']/value").text.replace("\n","")
        except AttributeError:
            # The extension Attribute has no value for this machine
            reqs = 'None'
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
        groupname = "Approved - "+policy
        group = self.jss.UserGroup(groupname)
        return group.id 

    def get_user_request(self, uun, UUID):
        user = self.get_user_object(uun)
        reqs = self._b64_to_object(user.find(".//extension_attribute[name='App Requests']/value").text)
        match = []
        if reqs:
            match = [r for r in reqs if r['UUID'] == UUID]
            print "Found existing req"
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
        user.save()
        self.send_confirmation(user, newreq)
        self.send_to_approver(newreq)

    def send_confirmation(self, user, newreq):
        with open(self.templates + '/template_email_confirmation.tmpl','r') as f:
            msg = f.read()

        reqdate = datetime.strptime(newreq['date'],
                                          "%Y-%m-%dT%H:%M:%S.%f")
        
        subject = "Request for {policy} submitted".format(policy=newreq['policy'])
        m = msg.format(policy=newreq['policy'],
                   date=reqdate.strftime("%Y-%m-%d, %H:%M"),
                   UUN=newreq['UUN'])
        self.contact_user(user.find('.//email').text, subject, m)

    def send_to_approver(self, newreq):
        with open(self.templates + '/template_email_to_approver.tmpl', 'r') as f:
            msg = f.read()

        reqdate = datetime.strptime(newreq['date'],
                                          "%Y-%m-%dT%H:%M:%S.%f")
        
        
        subject = "Request for {policy}".format(policy=newreq['policy'])
        m = msg.format(policy=newreq['policy'],
                       date=reqdate.strftime("%Y-%m-%d, %H:%M"),
                       UUN=newreq['UUN'],
                       msg=newreq['message'],
                       UUID=newreq['UUID'],
                       base_url=self.base_url)

        from_address = self.get_user_object(newreq['UUN']).find('.//email').text

        self.contact_user(newreq['approver'], subject, m, from_address)

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

    def contact_user(self, to, subject, message, us='donotreply@ed.ac.uk'):
        s = smtplib.SMTP('localhost')
        s.sendmail(us, to, "From: "+us+"\nTo:"+to+"\nSubject: "+subject+"\n\n"+message)
        #s.sendmail(us, to, "Subject: "+subject+"\n\n"+message)
        s.quit

    def _b64_to_object(self, blob):
        if blob is not None:
            return json.loads(base64.b64decode(blob))
        return []

    def _object_to_b64(self, requests):
        return base64.b64encode(json.dumps(requests))

    def harvest(self):
        computer_reqs = self.get_all_computer_requests()
        for req in computer_reqs:
            print 'Processing '+req['UUID']
            if not self.get_user_request(req['UUN'], req['UUID']):
                print "Adding user request "+req['UUID']
                self.add_user_request(req['UUN'], req)
