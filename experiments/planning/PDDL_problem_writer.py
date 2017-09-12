import re

_all_fds = set()
_all_files = set()
_all_ports = set()
_all_processes = set()

_fds_to_init = set()
_existing_fds = set()

_pddl_init_section = []

with_types = True

def _parse_path(path):
    newname = path.replace('/', '_').replace('.', '_').replace('{', '').replace('}', '').replace('@', '_').replace('+', '_')
    if newname[0] == '_':
        newname = newname[1:]
    return newname

def _extract_process(line):
    return _parse_path(line.strip().split(' ')[-1])

def _extract_port(tuple):
    return tuple.split(':')[-1]

def init_problem():
    global _all_fds
    global _all_files
    global _fds_to_port
    global _fds_to_process
    global _fds_to_init
    global _existing_fds
    global _pddl_init_section
    _all_fds = set()
    _all_files = set()
    _fds_to_port = set()
    _fds_to_process = set()
    _fds_to_init = set()
    _existing_fds = set()
    _pddl_init_section = []


def _get_filename(filename):
    if filename == '/var/log/fetchmail.log':
        return 'fetchmail_logfile'
    else:
        return _parse_path(filename)

def _init_file_socket(fd, line):
    _pddl_init_section.append('\t\t\t(' + 'file-fd' + ' ' + 'fd' + fd + ')')
    file_details = re.findall('(\(.+?\))', line)
    filename = re.findall('\(<f>(.*)\)', file_details[1])
    if filename:
        pddlfilename = filename[0]
        if pddlfilename == '/var/log/fetchmail.log':
            _pddl_init_section.append('\t\t\t(' + 'related-file' + ' ' + 'fd' + fd + ' ' + 'fetchmail_logfile' + ')')
        else:
            _all_files.add(_parse_path(pddlfilename))


def _init_inet6_socket(fd, line):
    _pddl_init_section.append('\t\t\t(' + 'inet-socket' + ' ' + 'fd' + fd + ')')
    socket_details = re.findall('(\(.+?\))', line)
    tuple = re.findall('\((.*)\)', socket_details[1])
    port = _extract_port(tuple[0])
    if port == '25' or port == '10025': # Before-filter SMTP server. Receive mail from the network and pass it to the content filter on localhost port 10025.
        _pddl_init_section.append('\t\t\t(' + 'smtp-connection' + ' ' + 'fd' + fd + ')')
    elif port == '143':
        _pddl_init_section.append('\t\t\t(' + 'imap-connection' + ' ' + 'fd' + fd + ')')
    else:
        _all_ports.add(port)


def _init_local_socket(syscall, fd, line1, line2):
    _pddl_init_section.append('\t\t\t(' + 'local-socket' + ' ' + 'fd' + fd + ')')
    process = ''
    if syscall == 'connect':
        process = _extract_process(line2)
    else:
        socket_details = re.findall('(\(.+?\))', line1)
        process_matches = re.findall('\(.* (.*)\)', socket_details[1])
        if process_matches:
            process = _parse_path(process_matches[0])
    _all_processes.add(process)


def _init_fd(syscall, fd, line1, line2):
    # WARNING: it means that nothing was done before it was closed, so we ignore it
    if syscall == 'close':
        _existing_fds.discard(fd)
        return

    _pddl_init_section.append('\t\t\t(' + 'opened' + ' ' + 'fd' + fd + ')')
    _existing_fds.add(fd)
    fdtype_groups = re.search('<(.+?)>', line1)
    if not fdtype_groups:
        return
    fdtype = fdtype_groups.group(1)
    if fdtype == 'u':
        _init_local_socket(syscall, fd, line1, line2)
    elif '6' in fdtype:
        _init_inet6_socket(fd, line1)
    elif '4' in fdtype:
        _init_inet6_socket(fd, line1) # need to be tested
    elif fdtype == 'f':
        _init_file_socket(fd, line1)

def _extract_socket_const_from_connect(line1, line2):
    fdtype = re.search('<(.+?)>', line1).group(1)
    if fdtype == 'u':
        process =  _extract_process(line2)
        _all_processes.add(process)
    elif '4' in fdtype or '6' in fdtype:
        port = _extract_port(line2.strip().split(' ')[-1])
        if port != '143' and port != '25':
            _all_ports.add(port)

def update_problem(syscall, args, line1, line2):
    if 'fd' in args:
        fd = args['fd']
        if int(fd) >= 0:
            _all_fds.add(fd)
        if syscall == 'socket' or syscall == 'open':
            if int(fd) >= 0:
                _existing_fds.add(fd)
        elif fd not in _existing_fds and int(fd) >= 0:
            _init_fd(syscall, fd, line1, line2)
        elif syscall == 'connect':
            _extract_socket_const_from_connect(line1, line2)
    elif syscall == 'poll':
        fd = args['fds'].split(':')[0]
        if fd and int(fd) >= 0:
            _all_fds.add(fd)
    elif syscall == 'stat':
        path = args['path']
        if path != '/etc/localtime':
            path = _parse_path(path)
            _all_files.add(path)
    elif syscall == 'clone':
        path = args['exe']
        if path != '/usr/bin/fetchmail':
            path = _parse_path(path)
            _all_files.add(path)

def _generate_object(object, type, with_type):
    if not with_type:
        return object + '\n'
    else:
        return object + ' - ' + type + '\n'

def generate_problem(problem_name, domain_name, goal):
    global with_types
    problem_str = ''
    problem_str += '(define (problem ' + problem_name + ')\n'
    problem_str += '\t(:domain ' + domain_name + ')\n'
    # objects:
    problem_str += '\t(:objects\n'
    for fd in _all_fds:
        if fd not in ['0', '1', '2']:
            problem_str += _generate_object('\t\t\t' + 'fd' + fd, 'fd', with_types)
    for file in _all_files:
        problem_str += _generate_object('\t\t\t' + file, 'path', with_types)
    for process in _all_processes:
        problem_str += _generate_object('\t\t\t' + process, 'path', with_types)
    for port in _all_ports:
        problem_str += _generate_object('\t\t\t' + 'p' + port, 'port', with_types)
    problem_str += '\t)\n'

    # init:
    # by default, the standard fd
    problem_str += '\t(:init\n'
    problem_str += '\n'.join(_pddl_init_section)
    problem_str += '\n\t)\n'

    # goal:
    problem_str += '\t(:goal\n' + goal + '\t)\n)\n'
    return problem_str