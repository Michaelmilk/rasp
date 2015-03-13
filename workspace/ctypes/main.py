import ctypes

def testInC():
    print "Running sum1000000Times() in C..."
    lib = ctypes.CDLL('./lib.so')
    lib.sum1000000Times.restype = ctypes.c_longlong
    print lib.sum1000000Times()
    print "Finished."

def testInPython():
    print "Running sum1000000Times() in python..."
    n = 0
    i = 1
    while i <= 1000000:
        n = n + i
        i += 1
    print n
    print "Finished."

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print "Param: [c|python]"
        sys.exit()

    if sys.argv[1] == 'c':
        testInC()
    elif sys.argv[1] == 'python':
        testInPython()
    else:
        print "Wrong param"

