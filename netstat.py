#!/usr/bin/env python
# pa
"""netstat adapter on macos fot tcollector """
import os
import subprocess
import sys
import time
from string import ascii_letters, digits

COLLECTION_INTERVAL = 60  # seconds

def compute_nbtab(line):
    """ return the number of tabs at beginning of line """
    nb = 0
    for l in line:
        if l == '\t':
            nb = nb + 1
        else:
            break
    return nb

def allowed(i):
    if i in ascii_letters or i in digits:
        return True
    else:
        return False

def only_ascii(item):
    """ remove non ascii char """
    checked = [i for i in item if allowed(i)]
    return ''.join(checked).lower()

def is_number(item):
    return len([i for i in item if i not in digits])==0

def cleaner(items):
    """ trim item """
    splitted = items.split()
    # print splitted
    cleaned = []
    number = None
    for item in splitted:
        if is_number(item):
            number = item
        elif item[0] is not '(' and item[len(item)-1] is not ')':
            cleaned.append(only_ascii(item))
    return (number, '_'.join(cleaned))

def emit_metric(ts, data):
    """ build a meaningfull metric with a data line """
    clean = [cleaner(d) for d in data]
    # print clean
    # check that clean[0] do not start with a number
    (n0,v0) = clean[0]
    if n0 is not None:
        # print 'error: do not understand metric' 
        return

    if len(clean) == 2:
        (n1,v1) = clean[1]
        return '{0}.{1} {2} {3}'.format(v0, v1, ts, n1)
    elif len(clean) == 3:
        (n1,v1) = clean[1]
        (n2,v2) = clean[2]
        return '{0}.{1}.{2} {3} {4}'.format(v0, v1, v2, ts, n2)

def test_cleaner():
    """ """
    ts = int(time.time())
    print only_ascii("tcp6:")
    print cleaner('13 bad neighbor advertisement messages')
    print cleaner('247413 datagrams (14816253 bytes) over IPv4')
    print emit_metric(ts, ['arp:', '22 ARP entries timed out'])
    print emit_metric(ts, ['ip:', '49196 packets sent from this host', '2 output packets discarded due to no route'])

def main():
    """nestats main loop"""

    while True:
        ts = int(time.time())
        # call netstat
        netstat_proc = subprocess.Popen(["netstat", "-s"], stdout=subprocess.PIPE)
        stdout, _ = netstat_proc.communicate()
        if netstat_proc.returncode == 0:

            # simple parser
            pntab = -1
            data = []
            for line in stdout.split("\n"):

                # count number of tab at bol
                ntab = compute_nbtab(line)
                sline = line[ntab:]
                #print 'pntab={0} ntab={1} len(data)={2} {3}'.format(pntab, ntab, len(data), sline)
                
                # the smart part
                # the data list is use as a queue to model the tree
                # tree navigation is given by the level of tabs at beg of line
                if ntab <= pntab:
                    metric =  emit_metric(ts, data)
                    if metric:
                        print metric
                    # pop list
                    for i in range(0, pntab-ntab+1):
                        data.pop()

                # add line
                data.append(sline)
                
                # postcondition
                pntab = ntab

        else:
            print >> sys.stderr, "netstat -s returned %r" % netstat_proc.returncode

        sys.stdout.flush()
        time.sleep(COLLECTION_INTERVAL)

if __name__ == "__main__":
    # test_cleaner()
    main()
