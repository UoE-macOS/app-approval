#!/usr/bin/python

from distutils.core import setup
import glob 

setup(name='python-jssapproval',
      version='0.2',
      description='Server-side componets to harvest and process policy requests on the JSS',
      long_description='Part of the JSS Approval framework',
      license='GPLv3',
      author='Geoff Lee, Stew Wilson',
      author_email='g.lee@ed.ac.uk',
      url='https://github.com/UoE-macOS/app-approval',
      packages=['jssapproval'],
      scripts=['jssapproval-harvest.py'],
      data_files=[('/etc/jssapproval', ['config.ini.example']),
      	          ('/usr/share/jssapproval/templates', glob.glob('jssapproval/templates/*')),
                  ('/usr/share/jssapproval', ['webapp.wsgi'])]
     )
