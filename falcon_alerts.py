#!/usr/bin/python
#
# Justin

import requests
from getpass import getpass
import json
# temp for testing
import pprint
pp = pprint.PrettyPrinter(indent=4)

########################
# Authentication Process
########################
falcon = requests.Session()
header = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US; q=0.7, en; q=0.3',
    'Cache-Control': 'no-cache',
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
    }
r1 = falcon.get('https://falcon.crowdstrike.com/login/', headers=header)
r2 = falcon.post('https://falcon.crowdstrike.com/api2/auth/csrf', headers=header)
header['X-CSRF-Token'] = r2.json()['csrf_token']
fh_uname = raw_input('FH Username (first.last): ') + '@rackspace.com'
fh_pass = getpass(prompt='FH Password: ')
fh_2fa = raw_input('FH 2FA: ')
auth_data = {'username': fh_uname, 'password': fh_pass, '2fa': fh_2fa}
r3 = falcon.post('https://falcon.crowdstrike.com/auth/login', headers=header, data=json.dumps(auth_data))
r4 = falcon.get('https://falcon.crowdstrike.com')
r5 = falcon.post('https://falcon.crowdstrike.com/api2/auth/verify', headers=header)
########################
# retrieve customer list
########################
try:
    customer_dict = r5.json()['customers']
    header['X-CSRF-Token'] = r5.json()['csrf_token']
except KeyError:
    print 'Check your credentials and rerun the program, exiting...'
    exit(2)
#########################################################################
# iterate through customer instances to retrieve, parse, and display data
#########################################################################
print '\n[*] {0} customer instances detected'.format(len(customer_dict))
print 'Searching for new alerts...'
for i in customer_dict:
    if r5.json()['user_customers'][i]['alias'] == 'IRON CLOUD':  # Rackspace corporate
        continue
    tmp = {'cid': i}
    s8 = falcon.post('https://falcon.crowdstrike.com/api2/auth/switch-customer', headers=header, json=tmp)
    s9 = falcon.post('https://falcon.crowdstrike.com/api2/auth/verify', headers=header)
    header['X-CSRF-Token'] = s9.json()['csrf_token']
    # There are 3 other v1 posts passed per customer with varying payloads.The dictionary below is required to return 
    # the necessary data; modifying it can break the request (needs more testing). I know it is not pep8 (too long)
    data_dict = {"name":"time","min_doc_count":0,"size":5,"type":"date_range","field":"last_behavior","date_ranges":[{"from":"now-1h","to":"now","label":"Last hour"},{"from":"now-24h","to":"now","label":"Last day"},{"from":"now-7d","to":"now","label":"Last week"},{"from":"now-30d","to":"now","label":"Last 30 days"},{"from":"now-90d","to":"now","label":"Last 90 days"}]},{"name":"status","min_doc_count":0,"size":5,"type":"terms","field":"status"},{"name":"severity","min_doc_count":0,"size":5,"type":"range","field":"max_severity","ranges":[{"from":80,"to":101,"label":"Critical","id":4},{"from":60,"to":80,"label":"High","id":3},{"from":40,"to":60,"label":"Medium","id":2},{"from":20,"to":40,"label":"Low","id":1},{"from":0,"to":20,"label":"Informational","id":0}]},{"name":"scenario","min_doc_count":0,"size":0,"type":"terms","field":"behaviors.scenario"},{"name":"assigned_to_uid","min_doc_count":1,"size":5,"type":"terms","field":"assigned_to_uid","missing":"Unassigned"},{"name":"host","min_doc_count":1,"size":5,"type":"terms","field":"device.hostname.raw","missing":"Unknown"},{"name":"triggering_file","min_doc_count":1,"size":5,"type":"terms","field":"behaviors.filename.raw"}
    s10 = falcon.post('https://falcon.crowdstrike.com/api2/detects/aggregates/detects/GET/v1', headers=header,
                      data=json.dumps(data_dict))
    if len(s10.json()['resources']) > 0:
        #pp.pprint(s10.json())  # full json data set!
        cust_data = s10.json()
        for bucket in cust_data['resources']:
            if bucket['name'] == 'status':
                for value in bucket['buckets']:
                    if value['label'] == 'new':
                        if 'count' in value:
                            print
                            print r5.json()['user_customers'][i]['name']  # customer name
                            print '*' * len(r5.json()['user_customers'][i]['name'])
                            print '{0} alert(s) detected!'.format(value['count'])
                #pp.pprint(bucket['buckets'])  # for testing!
print '\nSearch complete'
