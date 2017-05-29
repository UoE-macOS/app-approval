Introduction.

These are the server-side components for the jssapproval system. They don't do 
very much on their own, but when combined with a JamfPro JSS and the appropriate
groups and extension attributes they provide a mechanism for policies in the JSS
to require 'approval', and a workflow to allow to allow approval to be carried out
by arbitrary memers of the organistion, who do not need any access to the JSS.

Contents.

The server components come in the form of a python package, 'jssapproval', and 
associated files. The package contains a Flask web application (webapp.py), which
could be served in various ways. A sample wsgi script is included, which can be 
used to serve it via Apache and mod_wsgi.

A small script, 'jssapprovals-harvester.py', is used to 'harvest' application requests
from the JSS for processing.

Installation.

If you have downloaded the source from github, you can install it using

python setup.py install

or build a package appropriate to your operating sytem (only RHEL 7 has been tested)
with (for example)

python setup.py bdist_rpm

The python package will install to the default location for python libraries on your 
system, an example config file will be installed into /etc/jssapproval, and the harvester
script will be installed into the default location for binaries on your system. Template
files and the wsgi example file will go into the system data files location (eg. /usr/share)

Configuration.

The example file in /etc/jssapproval/config.ini.example should get you up and running. If you 
change the path to the template directory, you will need to provide copies of each of the 
templates found in /usr/share/jssapproval/templates

We assume you will use cron or watever is appropriate on your system to configure the harvester
to run at an appropriate interval. What this interval is will be specific to your 
environment but 5 minutes is possibly a reasonable starting point, unless you have a huge number
of machines. The time taken to run it scales linerly with the number of machines in your JSS.
 

