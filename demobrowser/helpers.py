import json
import urllib2
import urllib
import re
import socket
import requests

LOGS_TF_URL = "http://logs.tf/upload"

## Functions ##
def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("google.com", 80))
    return s.getsockname()[0]

def get_steam_userinfo(steam_id, api_key=None):
    if api_key is None:
        return {}
    options = {
        'key': api_key,
        'steamids': steam_id
    }
    url = 'http://api.steampowered.com/ISteamUser/' \
          'GetPlayerSummaries/v0001/?%s' % urllib.urlencode(options)
    rv = json.load(urllib2.urlopen(url))
    return rv['response']['players']['player'][0] or {}

def convert_id_to_community(steam_id):
    match = re.match("^.*([01]):(\d+)$", steam_id)
    if not match:
        return None
    if len(match.groups()) != 2:
        return None
    return (int(match.group(2) * 2)) + 76561197960265728 + int(match.group(1))

def do_upload_log(logfile, api_key, title=None, map=None):
    '''
    Perform the actual POST. Only include fields that are not None.

    Returns:
    success - True/False
    log_id  - -1 if Failure, logid if success
    msg     - Status msg
    '''
    payload = {'key': api_key}
    try:
        logfiles = {'logfile': open(logfile, 'r')}
    except IOError:
        # print "FAILED to upload log:"
        # print "File '%s' did not exist!" % logfile
        return False, -1, "File '%s' did not exist!" % logfile
    if map:
        payload['map'] = map
    if title:
        payload['title'] = title
    results = requests.post(LOGS_TF_URL, files=logfiles, data=payload).json()
    if not results.get('success', False):
        print "FAILED to upload log:"
        msg = results.get('error', 'UNKNOWN')
        print msg
        if msg == "Invalid API key":
            print "You can get an API Key here: http://logs.tf/uploader"
        return False, -1, msg
    # print "Great success!"
    # print "Log ID: %s" % results.get('log_id', 'UNKNOWN')
    # print "URL: http://logs.tf%s" % results.get('url', 'UNKNOWN')
    return True, results.get('log_id', 'UNKNOWN'), "Great Success!"