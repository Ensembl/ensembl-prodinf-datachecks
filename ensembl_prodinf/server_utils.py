import re
import subprocess

http_uri_regex = r"^(http){1}(s){0,1}(://){1}(.+){1}(:){1}(\d+){1}(/){1}(.+){0,1}$"
uri_regex = r"^(mysql://){1}(.+){1}(:.+){0,1}(@){1}(.+){1}(:){1}(\d+){1}(/){1}$"
db_uri_regex = r"^(mysql://){1}(.+){1}(:.+){0,1}(@){1}(.+){1}(:){1}(\d+){1}(/){1}(.+){1}$"    
email_regex = r"^(.+){1}(@){1}(.+){1}$",

def assert_http_uri(uri):
    if not re.search(http_uri_regex, uri):
        raise ValueError("Endpoint URL doesn't match pattern: http://server_name:port/")

def assert_mysql_uri(uri):
    if not re.search(uri_regex, uri):
        raise ValueError("MySQL URL doesn't match pattern: mysql://user(:pass)@server:port/")

def assert_mysql_db_uri(uri):
    if not re.search(db_uri_regex, uri):
        raise ValueError("MySQL database URL doesn't match pattern: mysql://user(:pass)@server:port/prod_db_name")   

def assert_email(email):
    if not re.search(email_regex, email):
        raise ValueError("Email doesn't match pattern: user@domain")

def get_load(host=None): 
    status = run_process('uptime', process_uptime, host)
    return status


def get_file_sizes(host=None, dir_name=None):     
    return run_process('"(cd ' + dir_name + ' && du -sm *)"', process_du, host)

 
def get_status(host=None, dir_name=None):
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
    m = up_pattern.match(line)
    if m:
        status['load_1m'] = float(m.group(1))
        status['load_5m'] = float(m.group(2))
        status['load_15m'] = float(m.group(3))


def process_free(status, line):
    if line.startswith("Mem:"):
        elems = line.split()
        status['memory_total_m'] = int(elems[1])
        status['memory_used_m'] = int(elems[2])
        status['memory_available_m'] = int(elems[3])
        status['memory_used_pct'] = float(format(100.0 * status['memory_used_m'] / status['memory_total_m'], '.1f'))


def process_df(status, line):
    if not line.startswith("Filesystem"):
        elems = line.split()
        status['disk_total_g'] = int(elems[1].replace('G', ''))
        status['disk_used_g'] = int(elems[2].replace('G', ''))
        status['disk_available_g'] = int(elems[3].replace('G', ''))
        status['disk_used_pct'] = float(format(100.0 * status['disk_used_g'] / status['disk_total_g'], '.1f'))


def process_ncores(status, line):
    elems = line.split()
    status['n_cpus'] = int(elems[0])


def process_du(status, line):
    elems = line.split()
    status[elems[1]] = long(elems[0])


def run_process(command, function, host=None):
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

