import os
import subprocess
import argparse
from PDDL_plan_writer import make_pddl_action
from PDDL_problem_writer import init_problem, update_problem, generate_problem
from sysdig_args_parser import get_syscall_args

FETCHMAIL_GMX_SUCCESS_PREDICATE = '(fetchmail-gmx-email-transferred)'
FETCHMAIL_SERVER_SUCCESS_PREDICATE = '(fetchmail-server-email-transferred)'
IMAP_LOGIN_SUCCESS_PREDICATE = '(imap-login-email-transferred)'
SMTPD_SUCCESS_PREDICATE = '(smtpd-email-transferred)'

WINDOWS = 'validate/'
MACOS = 'MacOSExecutables/'

running_os = WINDOWS
#running_os = MACOS

def get_goal():
    goal = '\t\t\t(or'
    goal += '\t\t\t\t' + FETCHMAIL_GMX_SUCCESS_PREDICATE + '\n'
    goal += '\t\t\t\t' + FETCHMAIL_SERVER_SUCCESS_PREDICATE + '\n'
    goal += '\t\t\t\t'+ IMAP_LOGIN_SUCCESS_PREDICATE + '\n'
    goal += '\t\t\t\t'+ SMTPD_SUCCESS_PREDICATE + '\n'
    goal += '\t\t\t)'
    return goal

behaviors = ['fetchmail-gmx', 'fetchmail-server', 'imap-login', 'smtpd']
# return the classification from the plan result
def get_classification_from_plan_result(plan_result):
    if FETCHMAIL_GMX_SUCCESS_PREDICATE in plan_result:
        return 'fetchmail-gmx'
    elif FETCHMAIL_SERVER_SUCCESS_PREDICATE in plan_result:
        return 'fetchmail-server'
    elif IMAP_LOGIN_SUCCESS_PREDICATE in plan_result:
        return 'imap-login'
    elif SMTPD_SUCCESS_PREDICATE in plan_result:
        return 'smtpd'
    else:
        return 'unimplemented'


def consistent_lines(line1, line2):
    # every 2 lines should have the same system call name in our context - multiprocess and multithread not handled
    syscall_name = line1.split(',')[8]
    if syscall_name != line2.split(',')[8]:
        print line1
        print line2
        print 'error in alignements'
        return False
    return True


def generate_problem_and_plan(csv_path, problem_path, plan_path):
    csv_file = open(csv_path, 'rb')
    init_problem()
    plan = ''
    while True:
        line1 = csv_file.readline()
        line2 = csv_file.readline()
        if not line2:
            break # EOF it not line2
        elif not consistent_lines(line1, line2):
            print csv_path
            break

        syscall_name = line1.split(',')[8]
        args = get_syscall_args(line1, line2, ',')
        update_problem(syscall_name, args, line1, line2)
        try:
            plan += make_pddl_action(syscall_name, args) + '\n'
        except Exception:
            print 'Error with file ' + csv_filepath

    goal = get_goal()
    problem = generate_problem('mailenv_problem', 'mailenv-syscalls', goal)
    with open(os.path.join(main_dir, plan_path), 'wb') as plan_file:
        plan_file.write(plan)
    with open(os.path.join(main_dir, problem_path), 'wb') as problem_file:
        problem_file.write(problem)


def execute_plan(csv_filename, domain_path, problem_path, plan_path):
    validator_dir = os.path.abspath('../../VAL/bin/' + running_os)
    validator_path = os.path.join(validator_dir, 'validate')
    try:
        plan_execution_res = subprocess.check_output([validator_path, '-v', domain_path, problem_path, plan_path])
        if 'Plan valid' in plan_execution_res:
            return get_classification_from_plan_result(plan_execution_res)
        else:
            return 'FAIL'
    except subprocess.CalledProcessError, e:
        return 'FAIL'
        # if 'Plan invalid' in e.output:
        #     print 'FAIL'
        # else:
        #     print 'The plan generated from ' + csv_filename + ' didn\'t execute corretly'


if __name__ == '__main__':	
    tmp_dirname = 'tmp'
    if not os.path.exists(tmp_dirname):
        os.makedirs(tmp_dirname)

    main_dir = os.path.abspath('.')
    tmp_dir = os.path.abspath('./' + tmp_dirname)
    domain_path = os.path.join(main_dir, 'mailenv-domain.pddl')
    problem_path = os.path.join(tmp_dir, 'problem_tmp.pddl')
    plan_path = os.path.join(tmp_dir, 'plan_tmp.plan')

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', type=str, help='execute a file')
    parser.add_argument('-d', type=str, help='execute all the files in the directory')
    parser.add_argument('-behavior', type=str, help='behavior of the samples in the directory')
    args = parser.parse_args()
    if (not args.f and not args.d) or (args.f and args.d):
        print 'Wrong usage, specify a file or a directory - look at the readme file'
    # testing 1 sample, print class of the sample
    if args.f:
        csv_filepath = args.f
        generate_problem_and_plan(csv_filepath, problem_path, plan_path)
        result = execute_plan(csv_filepath, domain_path, problem_path, plan_path)
        print args.f + ' ' + result 
    # testing directory containing one class, print number of correctly classified and misclassified 
    elif args.d and args.behavior:
        csv_dir = os.path.abspath(args.d)
        if args.behavior not in behaviors:
            print 'Implemented behaviors: ' + ', '.join(behaviors)
        else:
            correct = 0
            misclassified = 0
            total = 0
            for csv_filename in os.listdir(csv_dir):
                csv_filepath = os.path.join(csv_dir, csv_filename)
                generate_problem_and_plan(csv_filepath, problem_path, plan_path)
                result = execute_plan(csv_filename, domain_path, problem_path, plan_path)
                if args.behavior:
                    if result == args.behavior:
                        correct += 1
                    else:
                        misclassified += 1
                total += 1
                if total % 20 == 0:
                    print str(total) + ' samples tested...'
            print 'Total number of samples: ' + str(total)
            print 'Correctly classified samples: ' +  str(correct)
            print 'Misclassified samples: ' + str(misclassified)
    # testing directory, print class of each sample
    elif args.d:
        csv_dir = os.path.abspath(args.d)
        for csv_filename in os.listdir(csv_dir):
            csv_filepath = os.path.join(csv_dir, csv_filename)
            generate_problem_and_plan(csv_filepath, problem_path, plan_path)
            result = execute_plan(csv_filename, domain_path, problem_path, plan_path)
            print csv_filename + ' ' + result 
