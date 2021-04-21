import os
import sys
from shutil import copytree, ignore_patterns, copy, rmtree
import random
import string
import datetime
import filecmp
import io
import re
import fileinput



def init():
    path = os.getcwd()
    os.chdir(path)
    os.makedirs('.wit')
    os.chdir(path + '\\.wit')
    os.makedirs('images')
    os.makedirs('staging_area')


class NoWitFile(Exception):
    """Raised when no wit file """
    pass


def wit_path(path):
    # look for wit
    if os.path.isdir(path):
        os.chdir(path)
    else:
        os.chdir("\\".join(path.split("\\")[:-1]))
    flag = False
    wit_path = os.getcwd()
    while not flag:
        try:
            os.listdir().index('.wit')
            flag = True
        except ValueError:
            os.chdir(os.path.dirname(os.getcwd()))
            wit_path = os.getcwd()
            if len(wit_path) < 4:
                raise NoWitFile
    return wit_path


def add(src_path):
    dst_wit_path = wit_path(src_path)
    # case 1
    if dst_wit_path == src_path:
        dst_wit_path = dst_wit_path + '\\.wit\\staging_area'
        copytree(src=src_path, dst=dst_wit_path, dirs_exist_ok=True, ignore=ignore_patterns('.wit'))
    # case 2
    else:
        try:
            dst_wit_path = dst_wit_path + '\\.wit\\staging_area\\' + src_path.replace(dst_wit_path, "")
            copytree(src=src_path, dst=dst_wit_path, dirs_exist_ok=True, ignore=ignore_patterns('.wit'))
        except NotADirectoryError:
            try:
                copy(src=src_path, dst=dst_wit_path)
            except FileNotFoundError:
                os.chdir(wit_path(src_path) + '\\.wit\\staging_area')
                #####
                dst_wit_path = wit_path(src_path)

                makedirs = src_path.replace(dst_wit_path, "").split('\\')[1:]

                os.chdir(wit_path(src_path) + '\\.wit\\staging_area')
                print(os.getcwd())
                for dir in makedirs[:-1]:

                    if not os.path.isdir(os.getcwd() + '\\' + dir):
                        os.makedirs(dir)
                    os.chdir(os.getcwd() + '\\' + dir)

                copy(src=src_path, dst=os.getcwd())


def commit(message):
    try:
        path = wit_path(os.getcwd()) + '\\.wit\\images'
    except NoWitFile:
        return

    commit_id = ''  # folder name
    for i in range(40):
        commit_id = commit_id + random.choice(string.ascii_lowercase[0:6] + '123456789')

    os.chdir(path)
    os.makedirs(commit_id)
    file = open(commit_id + '.txt', 'w')

    try:
        ref_file = open(wit_path(os.getcwd()) + '\\.wit\\references.txt')
        ref = ref_file.readlines()[0].split('=')[1]
        parent = ref.rstrip('\n')
    except FileNotFoundError:
        parent = None

    date = datetime.datetime.now()
    date.strftime("%Y-%m-%d %H:%M:%S")
    file.write(f'parent={parent}\n date={str(date)}\n message={message}')
    file.close()

    copytree(src=wit_path(os.getcwd()) + '\\.wit\\staging_area',
             dst=wit_path(os.getcwd()) + '\\.wit\\images\\' + commit_id,
             dirs_exist_ok=True)

    os.chdir(wit_path(os.getcwd()) + '\\.wit')
    file = open('references.txt', 'w')
    file.write(f'HEAD={commit_id}\n master={commit_id}')
    file.close()


def current_coomit_id():
    try:
        w_path = wit_path(os.getcwd()) + '\\.wit\\'
    except NoWitFile:
        return
    os.chdir(w_path)
    file = open('references.txt', 'r')
    commit_id = file.readlines()[0].split('=')[1].rstrip('\n')
    return commit_id


def changes_to_be_committed():
    # work only if anccseor has .wit folder
    try:
        w_path = wit_path(os.getcwd()) + '\\.wit\\'
        org_path = wit_path(os.getcwd())
    except NoWitFile:
        return

    commit_id = current_coomit_id()
    commit_info = open(w_path + '\\images\\' + commit_id + '.txt', 'r')
    commit_time = commit_info.readlines()[1].split('=')[1].rstrip('\n')[:-7]  # get last time commit of commit

    namelist = []

    for root, dirs, files in os.walk(w_path + '\\staging_area'):
        for name in files:
            filepath = (os.path.join(root, name))
            filetime = (os.path.getmtime(filepath))
            if filetime > datetime.datetime.strptime(commit_time, "%Y-%m-%d %H:%M:%S").timestamp():
                namelist.append(name)

    return namelist


def changes_not_staged_for_commit():
    try:
        w_path = wit_path(os.getcwd()) + '\\.wit\\staging_area'
        org_path = wit_path(os.getcwd())
    except NoWitFile:
        return

    os.chdir(org_path)
    a = os.listdir()
    a.remove('.wit')
    org_path = org_path + "\\" + a[0]
    w_path = w_path + "\\" + a[0]
    dcmp = filecmp.dircmp(org_path, w_path)

    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    dcmp.report_full_closure()
    output = new_stdout.getvalue()
    sys.stdout = old_stdout
    s = output
    start = 'Differing files'
    end = ']'
    result_diff_files = re.findall('%s(.*)%s' % (start, end), s)
    diff_files = []
    for check in result_diff_files:
            diff_files.append(extract_text(check))

    start = 'Only in'
    end = ']'
    result_only_in = re.findall('%s(.*)%s' % (start, end), s)
    only_in_org = []
    for check in result_only_in:
        if check.find('staging_area')== -1:
            only_in_org.append(extract_text(check))


    return diff_files , only_in_org

def extract_text(txt):

    flag = False
    return_txt = ''

    for letter in txt:
        if letter == '[':
            flag = True
        if flag:
            return_txt = return_txt + letter
    return_txt = return_txt +']'
    return (return_txt)


def status():
    print(f'commit id:{current_coomit_id()}')
    print(f'Changes to be committed:{changes_to_be_committed()}')
    diff , onlyin = changes_not_staged_for_commit()
    print(f'diff files:{diff}')
    print(f'untracked files : {onlyin}')


def checkout(commit_id):
    try:
        w_path = wit_path(os.getcwd()) + '\\.wit\\images' + commit_id
        org_path = wit_path(os.getcwd())
    except NoWitFile:
        return
    os.chdir(org_path)
    a = os.listdir()
    a.remove('.wit')
    org_path = org_path + "\\" + a[0]

    diff, onlyin = changes_not_staged_for_commit()
    ctc = changes_to_be_committed()


    if diff == [] and onlyin == [] and ctc == []:

        print('true')
        os.chdir(wit_path(os.getcwd()))
        print(os.getcwd())
        rmtree(org_path)
        copytree(src=w_path, dst=org_path, dirs_exist_ok=True)
        st_path =  wit_path(os.getcwd()) + '\\.wit\\staging_area'
        rmtree(st_path)
        copytree(src=w_path, dst=st_path, dirs_exist_ok=True)


    w_path = wit_path(os.getcwd()) + '\\.wit\\'
    os.chdir(w_path)

    # Read in the file
    with open('references.txt', 'r') as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace(current_coomit_id(), commit_id)

    # Write the file out again
    with open('references.txt', 'w') as file:
        file.write(filedata)






if __name__ == '__main__':

    if sys.argv[1] == 'init':
        init()
    if sys.argv[1] == 'add':
        add(sys.argv[2])
    if sys.argv[1] == 'commit':
        commit(sys.argv[2])

    if sys.argv[1] == 'status':
        status()

    if sys.argv[1] == 'checkout':
        checkout(sys.argv[2])
