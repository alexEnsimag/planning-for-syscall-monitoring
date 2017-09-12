from PDDL_problem_writer import _parse_path

mailenv_integer_list = [1, 2, 3, 5, 6, 14, 15, 18, 29, 31, 34, 37, 39, 48, 50, 53, 54, 55, 56, 58, 59, 60, 61, 62, 63, 65, 92, 118, 121, 147]

FD_FAIL = 'fdFAIL'
int_FAIL = 'nFAIL'
int_EAGAIN = 'nEAGAIN'

syscall_without_args = ['statfs', 'setitimer', 'setsockopt', 'rt_sigaction', 'nanosleep']

def _get_ioctl_constant(request):
    if request == '541B':
        return 'FIONREAD'
    else:
        return 'COMMAND_NOT_SUPPORTED'

def _get_socket_domain(domain):
    if domain == '1':
        return 'AF_LOCAL'
    else:
        return 'SOCKTYPE_NOT_SUPPORTED'

def _get_process_name(process):
    if process == 'public/cleanup':
        return 'cleanup'
    elif process == '/usr/bin/fetchmail':
        return 'fetchmail'
    elif process == '/etc/localtime':
        return 'etc_localtime'
    else:
        return _parse_path(process)

def _get_integer_constant(integer):
    if int(integer) == -11:
        return int_EAGAIN
    elif int(integer) < 0:
        return int_FAIL
    elif int(integer) in mailenv_integer_list:
        return 'n' + integer
    else:
        return 'n0'

def _get_fd_constant(fd) :
    if fd != 'syslog' and int(fd) <0:
        return 'FD_FAIL'
    return 'fd' + fd

def make_pddl_action(syscall, args):
    # writing args to planning action parameters
    actionparams = ''
    if syscall == 'poll':
        if args['fds']: #WARNING: we ignore an action where there are no fd specifieds - error in sysdig ?
            fd = args['fds'].split(':')[0]
            actionparams = _get_fd_constant(fd) + ' ' + _get_integer_constant(args['res'])
        else:
            return '(notimplemented)'
    elif syscall == 'read' or syscall == 'write' or syscall == 'sendto':
        res = 'n0'
        if 'res' in args:
            res = _get_integer_constant(args['res'])
            if res != int_FAIL and res != int_EAGAIN:
                res = max(res, _get_integer_constant(args['size']))
        actionparams = _get_fd_constant(args['fd']) + ' ' + res
    elif syscall == 'socket':
        actionparams = _get_socket_domain(args['domain']) + ' ' + _get_fd_constant(args['fd'])
    elif syscall == 'connect':
            if len(args['tuple'].split(' ')) > 1:
                actionparams = _get_fd_constant(args['fd']) + ' ' + _get_process_name(args['tuple'].split(' ')[1]) + ' ' + 'NO_PORT' + ' ' + _get_integer_constant(args['res'])
            else:
                actionparams = _get_fd_constant(args['fd']) + ' ' +'NO_PATH' + ' ' + 'p' + args['tuple'].split(':')[-1] + ' ' + _get_integer_constant(args['res'])
    elif syscall == 'ioctl':
        actionparams = _get_fd_constant(args['fd']) + ' ' + _get_ioctl_constant(args['request']) + ' ' + _get_integer_constant(args['res'])
    elif syscall == 'close':
        actionparams = _get_fd_constant(args['fd']) + ' ' + _get_integer_constant(args['res'])
    elif syscall == 'pipe':
        actionparams = _get_fd_constant(args['fd1']) + ' ' + _get_fd_constant(args['fd2']) + ' ' + _get_integer_constant(args['res'])
    elif syscall == 'clone':
        actionparams = _get_process_name(args['exe']) + ' ' +  _get_integer_constant(args['res'])
    elif syscall == 'epoll_wait':
        actionparams = _get_integer_constant(args['res'])
    elif syscall == 'recvfrom':
        actionparams = _get_fd_constant(args['fd']) + ' ' +  _get_integer_constant(args['res'])
    elif syscall == 'stat':
        actionparams = _get_process_name(args['path']) + ' ' +  _get_integer_constant(args['res'])
    else:
        if syscall not in syscall_without_args:
            syscall = 'notimplemented'

    # writing planning action
    if actionparams == '':
        return '(' + syscall + ')'
    else:
        return '(' + syscall + ' ' + actionparams + ')'