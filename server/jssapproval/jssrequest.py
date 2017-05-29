from datetime import datetime
from jsstools import JSSTools


class JSSRequest(object):
    """ Class for handling individual application requests
        Requests are held as JSON blobs in the user objects of the JSS
    """

    def __init__(self, UUID, uun=None):
        self.j = JSSTools(config_file='/localdisk/macated/config.ini')

        if uun:
            self.attributes = self.j.get_user_request(uun, UUID)[0]
            self.user = self.j.get_user_object(uun)
        else:
            self.attributes = self.j.get_user_requests_all(UUID)[0]
            self.user = self.j.get_user_object(self.attributes['UUN'])

        if 'status' not in self.attributes:
            self.attributes['status'] = 'Pending'

    def approve(self, approver='No approver specified'):
        if self.attributes['status'] != 'Pending':
            raise ValueError("Request already handled: "+self.attributes['status'])

        try:
            # Add user to group, then update the request
            self.j.approve(self.user, self.attributes['policy'])
            self.attributes['status'] = 'Approved'
            self.attributes['actioned_at'] = datetime.now().isoformat()
	    self.attributes['actioned_by'] = approver
        except ValueError, e:
            self.attributes['error'] = str(e)
            raise e
        finally:
            self.j.update_user_request(self.user, self.attributes)


        subject = "Request for {} approved".format(self.attributes['policy'])
        with open(self.j.templates + '/template_email_approved.tmpl') as f:
            msg = f.read()

        m = msg.format(**self.attributes)
        self.j.contact_user(self.user.find('.//email').text, subject, m)


    def update(self):
        self.j.update_user_request(self.user, self.attributes)

    def deny(self, reason="Request denied", approver='No approver specified'):
        if self.attributes['status'] != 'Pending':
            raise ValueError("Request already handled: "+self.attributes['status'])

        self.attributes['status'] = 'Denied'
        self.attributes['actioned_at'] = datetime.now().isoformat()
        self.attributes['actioned_by'] = approver

        subject = "Request for {} denied".format(self.attributes['policy'])
        with open(self.j.templates + '/template_email_denied.tmpl','r') as f:
            msg = f.read()

        m = msg.format(denial_reason=reason,
		       **self.attributes)
        self.j.contact_user(self.user.find('.//email').text, subject, m)

        self.j.update_user_request(self.user, self.attributes)
