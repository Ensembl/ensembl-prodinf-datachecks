import re
import subprocess
from urllib.parse import urlparse


db_netloc_re = re.compile(r'^.+@.+:\d+$')
email_re = re.compile(r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$')


"""
Utilities for dealing with REST and database servers
"""

def assert_http_uri(uri):
    """Check supplied URI matches http"""
    parsed_uri = urlparse(uri)
    if not (parsed_uri.scheme.startswith('http') and parsed_uri.netloc and parsed_uri.path):
        raise ValueError("Endpoint URL doesn't match pattern: http(s)://server-name(:port)/")

def assert_mysql_uri(uri):
    """Check supplied URI matches MySQL server"""
    parsed_uri = urlparse(uri)
    valid_netloc = db_netloc_re.match(parsed_uri.netloc)
    if not (parsed_uri.scheme == 'mysql' and valid_netloc and len(parsed_uri.path) == 1):
        raise ValueError("MySQL URL doesn't match pattern: mysql://user(:pass)@server:port/")

def assert_mysql_db_uri(uri):
    """Check supplied URI matches MySQL database"""
    parsed_uri = urlparse(uri)
    valid_netloc = db_netloc_re.match(parsed_uri.netloc)
    if not (parsed_uri.scheme == 'mysql' and valid_netloc and len(parsed_uri.path) > 2):
        raise ValueError("MySQL database URL doesn't match pattern: mysql://user(:pass)@server:port/prod_db_name")

def assert_email(email):
    """Check supplied string is an email address"""
    if not email_re.match(email):
        raise ValueError("Email doesn't match pattern: user@domain")

def get_load(host=None):
    """Find load by on the supplied host by ssh (or on localhost if no host is supplied)
    """
    # load obtained from uptime
    status = run_process('uptime', process_uptime, host)
    return status

def get_file_sizes(host=None, dir_name=None):
    """Find file sizes in the supplied directory on the supplied host by ssh (or on localhost if no host is supplied)
    """
    # determine file sizes with du
    return run_process('"(cd ' + dir_name + ' && du -sm *)"', process_du, host)

def get_status(host=None, dir_name=None):
    """Base entry point for getting all status for a host, returned as a dict
    Arguments:
      host - optional remote host (must be accessible via ssh)
      dir_name - directory to check disk space on
    """
    # determine file sizes with du
    status = {}
    if(host != None):
        status['host'] = host
    if(dir_name != None):
        status['dir'] = dir_name
        status.update(run_process('df -P -BG ' + dir_name, process_df, host))
    status.update(run_process('free -m', process_free, host))
    status.update(run_process('uptime', process_uptime, host))
    status.update(run_process('grep -c "^processor" /proc/cpuinfo', process_ncores, host))
    return status

up_pattern = re.compile('.* load average: ([0-9.]+), ([0-9.]+), ([0-9.]+)')


def process_uptime(status, line):
    """Internal method to parse output of uptime and add to status hash"""
    m = up_pattern.match(line)
    if m:
        status['load_1m'] = float(m.group(1))
        status['load_5m'] = float(m.group(2))
        status['load_15m'] = float(m.group(3))


def process_free(status, line):
    """Internal method to parse output of free and add to status hash"""
    if line.startswith("Mem:"):
        elems = line.split()
        # memory is added in Mb
        status['memory_total_m'] = int(elems[1])
        status['memory_used_m'] = int(elems[2])
        status['memory_available_m'] = int(elems[3])
        status['memory_used_pct'] = float(format(100.0 * status['memory_used_m'] / status['memory_total_m'], '.1f'))


def process_df(status, line):
    """Internal method to parse output of df and add to status hash"""
    if not line.startswith("Filesystem"):
        elems = line.split()
        # space is added in Gb
        status['disk_total_g'] = int(elems[1].replace('G', ''))
        status['disk_used_g'] = int(elems[2].replace('G', ''))
        status['disk_available_g'] = int(elems[3].replace('G', ''))
        status['disk_used_pct'] = float(format(100.0 * status['disk_used_g'] / status['disk_total_g'], '.1f'))


def process_ncores(status, line):
    """Internal method to parse output of cpuinfo file and add to status hash"""
    elems = line.split()
    status['n_cpus'] = int(elems[0])


def process_du(status, line):
    """Internal method to parse output of du and add to status hash"""
    elems = line.split()
    status[elems[1]] = int(elems[0])


def run_process(command, function, host=None):
    """Internal common method used to execute supplied command on supplied host, and parse with supplied function"""
    status = {}
    if host != None:
        command = 'ssh -q ' + host + ' ' + command
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in p.stdout.readlines():
        function(status, line)
    retval = p.wait()
    if retval != 0:
        raise OSError("Could not execute command " + command)
    return status

