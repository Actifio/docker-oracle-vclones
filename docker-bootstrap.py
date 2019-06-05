# Copyright 2018 <Kosala Atapattu kosala.atapattu@actifio.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included 
# in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE 
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import re
import logging
import time
import signal
import subprocess

try: 
  from Actifio import Actifio
except ImportError:
  raise ("Unable to import actifio module.")

try: 
  from jinja2 import Template
except ImportError:
  raise ("Unable to import jinja2 Template.")


# this section extracts parameters from environment variables
act_appliance = os.environ.get('ACT_APPLIANCE')
act_user = os.environ.get('ACT_USER')
act_pass = os.environ.get('ACT_PASS')

act_appname = os.environ.get('ACT_APPNAME')
act_srchost = os.environ.get('ACT_SRCHOST')

act_targetsid = os.environ.get('ORACLE_SID')
act_orahome = os.environ.get('ORACLE_HOME')
act_orauser = os.environ.get('ORACLE_USER')
act_tnsadmin = os.environ.get('TNS_ADMIN')

myhostname = os.environ.get('HOSTNAME')
############################################################

if act_orauser is None:
  act_orauser = "oracle"

if act_tnsadmin is None:
  act_tnsadmin = act_orahome + "/network/admin"

# define a appliance instance
appliance = Actifio(act_appliance, act_user, act_pass)

# look up the oracle app

oraapps = appliance.get_applications(appname=act_appname, hostname=act_srchost, appclass="Oracle")

if len(oraapps) != 1:
  raise ("ERROR: not expecting to filter more than one application")

# greb the target host from /act/config

hostid = re.compile(r'^HostId\s+=\s+(.*)$')

try:
  with open("/act/config/connector.conf") as configfile:
    for line in configfile:
      hostname_match = hostid.search(line)
      if hostname_match is not None:
        hostuniqname = hostname_match.group(1)
        break
except IOError:
  raise ("ERROR: /act/config/connector.conf is not found. Have you bind mount /act?")
 
# lookfor a target host

targethosts = appliance.get_hosts(uniquename=hostuniqname)

if len(targethosts) != 1:
  raise ("ERROR: returned hosts are not equal to 1")

job,image = appliance.simple_mount(source_application=oraapps[0],target_host=targethosts[0], label="DOCKER CONTAINER")

while job.status == "running":
  time.sleep(10)
  job.refresh()

# now the job is complete
# find the mount point

for folder in os.listdir("/act/mnt/"):
  if os.path.isdir("/act/mnt/" + folder) and (job.jobname in folder):
    if os.path.isdir("/act/mnt/" + folder + "/datafile"):
      act_datamount = "/act/mnt/" + folder
    elif os.path.isdir("/act/mnt/" + folder + "/archivelog"):
      act_lsmount = "/act/mnt/" + folder


# run the oracle mount script

appaware_command_j2 = Template("su - {{ orauser }} -c 'export databasesid={{ orasid }};export orahome={{ orahome }};export tnsadmindir={{ tnsadminpath }};export username={{ orauser }};export isrestore=false;export isgrandchild=false;export isremount=false;export imageLogOffset=1;export ischild=false;export opname=mount;/act/act_scripts/oracleclone/OracleAppMount.sh {{ orasid }} {{ orahome }} {{ datamount}}'")
appaware_command = appaware_command_j2.render(orauser=act_orauser, orasid=act_targetsid, orahome=act_orahome, tnsadminpath=act_tnsadmin, datamount=act_datamount)

# start oracle listner
lsnrctl_j2 = Template("su - {{ orauser }} -c 'ORACLE_HOME={{ orahome }} lsnrctl start'")
lsnrctl_start_cmd = lsnrctl_j2.render(orauser=act_orauser, orahome=act_orahome)

# spin up in a subprocesses
subprocess.call(appaware_command,shell=True)
subprocess.call(lsnrctl_start_cmd,shell=True)

abort_oracle_j2 = Template("su - {{ orauser }} -c 'kill -9 -1'")
abort_oracle = abort_oracle_j2.render(orauser=act_orauser)

for img in job.sourceid.split (","):
  mounted_image = appliance.get_images(backupname=img)
  if mounted_image[0].jobclass == "mount":
    mountedimage = mounted_image[0]

def unmountthemount (SignNum, frame):
  os.system(abort_oracle)
  appliance.unmount_image(image=mountedimage)

signal.signal(signal.SIGINT, unmountthemount)    
signal.signal(signal.SIGTERM, unmountthemount)    

# don't quit, and listen
while True:
  time.sleep(10)