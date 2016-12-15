#!/bin/sh
#################################################################################
# This JSS extension attribute concatenates together the contents
# of files stored in the $store directory.
#
# It is assumed that the files will contain a valid JSON object and
# nothing else. For example:
#
# {"date": "2016-12-15T11:42:49.002978", "message": "hi there!", \
#  "UUN": "glee1", "UUID": "fcf257ee-ebe9-410b-a769-ac29f346ff05"}
#
# The result of the concatenation is base64 encoded for ease of transport.
# This extension attribute is intended for use with the other tools
# found at: https://github.com/UoE-macOS/app-approval/
#
# Author: <g.lee@ed.ac.uk>
#################################################################################
store="/Library/MacAtED/AppRequests"

if ! ls ${store}/*.apprequest &>/dev/null
then
 requests="None"
else
 requests=$(/bin/echo -n "[ $(awk 'FNR==1 && NR > 1{print ","}1' ${store}/*.apprequest) ]" | tr -d "\n" | openssl enc -base64)
fi

/bin/echo -n "<result>"
/bin/echo -n ${requests}
/bin/echo "</result>"
