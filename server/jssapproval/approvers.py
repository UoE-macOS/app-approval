import json


class Approvers(object):
    """ Wrapper for getting & returning approvers
    """

    def __init__(self, approvers_file):

        # Right now, expecting a text file that contains a JSON
        # dict, with a list of approvers by each key e.g.
        # {'S48': 'seesup@ed.ac.uk',
        #  'ENG': 'seesup@ed.ac.uk'}
        with open(approvers_file, 'r') as f:
            self.approvers = json.load(f)

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
            raise KeyError("No approver defined for area "+area)