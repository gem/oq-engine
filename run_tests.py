#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import nose

if __name__ == "__main__":
    sys.path.append("%s/tests" % os.path.abspath(os.path.curdir))
    args = sys.argv
    args.remove("run_tests.py")
    args = ["nosetests"] + args
    nose.run(defaultTest="tests", argv=args)
