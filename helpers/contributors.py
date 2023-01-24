#!/usr/bin/env python3
import sys
import re


def usage(ret):
    print("""
USAGE:
    %s input_file [> output_file]
""" % sys.argv[0])
    sys.exit(ret)


def main():
    if len(sys.argv) != 2 or sys.argv[1] == '-h' or sys.argv[1] == '--help':
        usage(1)

    max_name = -1
    max_gh = -1
    l_arr = []

    is_header = True
    with open(sys.argv[1]) as fin:
        for lin in fin:
            lin = lin.rstrip()
            if is_header is True and lin != "Code":
                l_arr.append([lin])
                continue
            else:
                is_header = False

            l_mod = re.sub(' +', ' ', lin)
            l_items = l_mod.split(' ')
            l_arr.append(l_items)
            n_items = len(l_items)
            if n_items >= 4:
                year = l_items[n_items - 1]
                month = l_items[n_items - 2]

                if l_items[n_items - 3][0:2] == "(@":
                    gh_account = l_items[n_items - 3]
                    max_gh = (max_gh if max_gh > len(gh_account)
                              else len(gh_account))
                    name = ' '.join(l_items[0:n_items - 3])
                else:
                    name = ' '.join(l_items[0:n_items - 2])
                    gh_account = ""
                max_name = max_name if max_name > len(name) else len(name)
    for l_items in l_arr:
        n_items = len(l_items)
        if n_items >= 4:
            year = l_items[n_items - 1]
            month = l_items[n_items - 2]

            if l_items[n_items - 3][0: 2] == "(@":
                gh_account = l_items[n_items - 3]
                name = ' '.join(l_items[0:n_items - 3])
            else:
                gh_account = ""
                name = ' '.join(l_items[0:n_items - 2])
            fmt = "%% -%ds  %% -%ds %%s %%s" % (max_name, max_gh)
            print(fmt % (name, gh_account, month, year))
        else:
            # import pdb ; pdb.set_trace()
            print(' '.join(l_items))


main()
