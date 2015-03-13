# C in Python(using ctypes)

[TOC]

## 参考

http://www.ibm.com/developerworks/cn/linux/l-cn-pythonandc/

https://docs.python.org/2/library/ctypes.html

## Memo

Python自带了[ctypes]模块进行C动态链接库(Windows中.dll，Linux中.so)和程序的调用。

## 记录

在目录`~/workspace/ctypes`:

编写C程序：`nano lib.c`

```c
#include <stdio.h>

int sum(int a, int b) {
    return a + b;
}

long long sum1000Times(void) {
    long long i;
    long long n;
    n = 0;
    for (i = 1; i <= 1000000; i ++) {
        n = n + i;
    }
    return n;
}

void printSomething(void) {
    printf("Hello world in C module\n");
    return;
}

int main(int argc, char** argv) {
    printSomething();
    return 0;
}
```

编译成可执行文件：`gcc -O2 -Wall -o lib.elf lib.c`

编译成动态链接库：`gcc -O2 -Wall -fPIC -shared -o lib.so lib.c`

编写python程序：`nano main.py`

```python
import ctypes

def testInC():
    print "Running sum1000Times() in C..."
    lib = ctypes.CDLL('./lib.so')
    lib.sum1000Times.restype = ctypes.c_longlong
    print lib.sum1000Times()
    print "Finished."

def testInPython():
    print "Running sum1000Times() in python..."
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
```

## 测试

测试由`main.py`调用`lib.so`中的`sum1000000times()`的运行时间：`time python main.py c`

输出

```
Running sum1000000Times() in C...
500000500000
Finished.

real    0m0.275s
user    0m0.220s
sys     0m0.040s
```

测试`main.py`中自带的`testInPython()`的运行时间：`time python main.py python`

输出

```
Running sum1000000Times() in python...
500000500000
Finished.

real    0m3.467s
user    0m3.390s
sys     0m0.050s
```

- - -

[ctypes]: https://docs.python.org/2/library/ctypes.html

