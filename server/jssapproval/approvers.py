import json
import urllib2
import base64


class Approvers(object):
    """ Wrapper for getting & returning approvers
    """

    def __init__(self, url, user, password):
        if url[:7] == "file://":
            with open(url[7:], 'r') as f:
                self.approvers = json.load(f)
        else:
            request = urllib2.Request("url")
            base64string = base64.encodestring('%s:%s' % (user, password)).replace('\n', '')
            request.add_header("Authorization", "Basic %s" % base64string)   
            self.approvers = json.load(urllib2.urlopen(request))

    def get_approver(self, host):
        
        if host[-8:] == 'ed.ac.uk':
            area = host.split('.')[-4].upper()
        elif '-' in host:
            area = host.split('-')[0].upper()
        else:
            #raise ValueError("Machine name has no area identifier")
            area = "No area identifier"

        try:
            approver = self.approvers[area]
        except KeyError, e:
            # No approver defined; kick it to Helpline
            approver = 'is.helpline@ed.ac.uk'
        
        # return approver
        print area + ":\t" + approver

        return "g.lee@ed.ac.uk"