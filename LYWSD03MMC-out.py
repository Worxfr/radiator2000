#!/usr/bin/python3

import sys
import os

PATH = "/dev/shm/radiator/"
ACTUAL = "ACTUAL"


if not os.path.exists(PATH): 
    os.mkdir(PATH)
ACTUAL_FILE =  open(os.path.join(PATH, ACTUAL), 'w+')

ACTUAL_FILE.write(sys.argv[3])

ACTUAL_FILE.close()
