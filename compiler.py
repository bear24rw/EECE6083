#! /usr/bin/env python

import sys
import argparse
import subprocess

from src.scanner import Scanner
from src.parser import Parser
from src.gen import Gen

argparser = argparse.ArgumentParser(description='EECS 6083 Compiler')

argparser.add_argument('filename', help='input .src file')
argparser.add_argument('-c', '--c_only', action='store_true', help='only generate .c file, do not compile it')
argparser.add_argument('-r', '--run', action='store_true', help='run the program after compiling it')
args = argparser.parse_args()

s_filename = args.filename
c_filename = args.filename.rsplit(".", 1)[0] + '.c'
o_filename = args.filename.rsplit(".", 1)[0]

gen = Gen()
scanner = Scanner(s_filename)
parser = Parser(scanner, gen)

if scanner.has_errors or parser.has_errors:
    print "-"*50
    print "BUILD FAILED"
    sys.exit(1)

gen.write_file(c_filename)

if args.c_only:
    sys.exit(0)

return_code = subprocess.call(['gcc', '-m32', '-Wno-int-to-pointer-cast', '-Wno-pointer-to-int-cast', '-o', o_filename, '-I', 'runtime', 'runtime/runtime.c', c_filename])

if return_code == 1:
    print "GCC ERROR"
    sys.exit(return_code)

if args.run:
    subprocess.call([o_filename])
