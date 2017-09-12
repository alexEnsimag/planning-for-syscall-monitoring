import re

# WARNING: doesn't keep consecutive spaces in the data argument (only one instead)
def _build_argument_dictionary(arguments):
    argdict = {}
    arglist = arguments.split(' ')
    if arglist[0]:
        i = 0
        while i < len(arglist):
            if arglist[i] == 'syslog':
                argdict['fd'] = arglist[i]
            else:
                if len(arglist[i].split('=')) < 2:
                    continue
                key = arglist[i].split('=')[0]
                val = arglist[i].split('=')[1]
                argdict[key] = val
                if key == 'data' or key == 'msg':
                    val = val + ' ' + ' '.join(arglist[i:])
                    argdict[key] = val
                    break
                if key == 'tuple' and val != 'NULL': # tuple is null, nothing to get from it
                    if len(arglist) > 2: # local socket
                        val = val + ' ' + arglist[i+1]
                        argdict[key] = val
                        i = i + 1
                    else: # internet socket
                        argdict[key] = val
            i += 1
    return argdict

def _get_line_args(line, separator):
    # split line by separator and clean escape characters
    line = re.sub("\(.*?\)", "", line)
    arguments = ' '.join(line.split(separator)[9:])
    arguments = arguments.strip()
    if arguments and arguments[0] == '"':
        arguments = arguments[1:len(arguments) - 1].strip()
    return _build_argument_dictionary(arguments)

def get_syscall_args(line1, line2, separator):
    argsline1 = _get_line_args(line1, separator)
    argsline2 = _get_line_args(line2, separator)
    argsline2.update(argsline1)
    return argsline2