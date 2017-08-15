import json, urllib2, base64


class Approvers(object):
    """ Wrapper for getting & returning approvers
    """

    def __init__(self, url, user, password):
        request = urllib2.Request("url")
        base64string = base64.encodestring('%s:%s' % (user, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)   
        self.approvers = json.load(result = urllib2.urlopen(request))

    def get_approver(self, host):
        return "g.lee@ed.ac.uk"
        
        if host[-8:] == 'ed.ac.uk':
            area = host.split('.')[-4].upper()
        elif '-' in host:
            area = host.split('-')[0].upper()
        else:
            raise ValueError("Machine name has no area identifier")

        try:
            return self.approvers[area]
        except KeyError, e:
            # No approver defined; kick it to Helpline
            return 'is.helpline@ed.ac.uk'