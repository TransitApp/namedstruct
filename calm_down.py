import sys
import py.test

sys.path = sys.path[1:]
py.test.main(sys.argv[1:])
