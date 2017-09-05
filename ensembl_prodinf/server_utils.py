import re
import subprocess
import os

def get_status(host=None,dir=None):
    status = {}
    if(dir!=None):
        status.update(run_process('df -hP '+dir,process_df, host))
    status.update(run_process('free -m',process_free, host))
    status.update(run_process('uptime',process_uptime, host))
    status.update(run_process('grep -c "^processor" /proc/cpuinfo',process_ncores, host))
    return status

up_pattern = re.compile('.* load average: ([0-9.]+), ([0-9.]+), ([0-9.]+)')
def process_uptime(status, line):
    m = up_pattern.match(line)
    if m:
        status['load_1m'] = m.group(1)
        status['load_5m'] = m.group(2)
        status['load_15m'] = m.group(3)

def process_free(status, line):
    if line.startswith("Mem:"):
        elems = line.split()
        status['memory_total'] = elems[1]+"M"
        status['memory_used'] = elems[2]+"M"
        status['memory_available'] = elems[3]+"M"

def process_df(status, line):
    if not line.startswith("Filesystem"):
        elems = line.split()
        status['disk_total'] = elems[1]
        status['disk_used'] = elems[2]
        status['disk_available'] = elems[3]

def process_ncores(status, line):
    elems = line.split()
    status['n_cpus'] = elems[0]

def run_process(command, function, host=None):
    status = {}
    if host!=None:
        command = 'ssh '+host+' '+command
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in p.stdout.readlines():
        function(status, line)
    retval = p.wait()
    if retval!=0:
        raise OSError("Could not execute command "+command)
    return status


