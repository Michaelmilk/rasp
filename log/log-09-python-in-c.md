# Python in C(using Cython)

[TOC]

## 参考

http://cython.org/

http://blog.csdn.net/gzlaiyonghao/article/details/4561611

http://stackoverflow.com/questions/22589868/call-python-code-from-c-via-cython

http://stackoverflow.com/questions/5005363/undefined-reference-to-sin-in-c

## Memo

[Cython]是使用混搭C和Python语法的代码，用来生成C扩展(.so)的编译器。

> 先用Python编写程序，然后看它是否能够满足需要。大多数情况下，它的性能已经足够好了……但有时候真的觉得慢了，那就使用分析器找到瓶颈函数，然后用cython重写，很快就能够得到更高的性能。

## 记录

安装Cython：`pip install Cython`

安装Cython需要极长时间。使用`Ctrl-Z`和`bg`命令可以让任务在后台运行。

目录`~/workspace/cython`：

编写python版测试程序：`nano py/lib.py`

```python
import math

def great_circle(lon1, lat1, lon2, lat2):
    radius = 3956
    x = math.pi/180.0

    a = (90.0-lat1)*(x)
    b = (90.0-lat2)*(x)
    theta = (lon2-lon1)*(x)
    c = math.acos((math.cos(a)*math.cos(b)) + (math.sin(a)*math.sin(b)*math.cos(theta)))

    return radius*c

def test100000Times():
    lon1, lat1, lon2, lat2 = -72.0, 34.3, -61.6, 54.2
    num = 100000

    print "Test in pure python, 100000 times:"
    a = 0
    while num > 0:
        a = great_circle(lon1, lat1, lon2, lat2)
        num -= 1;
    print "Done, value=", a

if __name__ == "__main__":
    test100000Times()
```

编写cython版测试程序：`nano pyx/lib.pyx`。

```cython
cdef extern from "math.h":
    float cosf(float theta)
    float sinf(float theta)
    float acosf(float theta)

# Still a python function defination
def great_circle(float lon1, float lat1, float lon2, float lat2):
    cdef float radius = 3956.0
    cdef float pi = 3.14159265
    cdef float x = pi/180.0
    cdef float a, b, theta, c
    
    a = (90.0-lat1)*(x)
    b = (90.0-lat2)*(x)
    theta = (lon2-lon1)*(x)
    c = acosf((cosf(a)*cosf(b)) + (sinf(a)*sinf(b)*cosf(theta)))
    
    return radius*c

cdef public void test100000Times():
    lon1, lat1, lon2, lat2 = -72.0, 34.3, -61.6, 54.2
    num = 100000
    
    print "Test in cython, 100000 times:"
    a = 0
    while num > 0:
        a = great_circle(lon1, lat1, lon2, lat2)
        num -= 1;
    print "Done, value=", a
    
if __name__ == "__main__":
    test100000Times()
```

编写调用cython模块的C程序：`nano pyx/main.c`

```c
#include <stdio.h>
#include <Python.h>
#include "lib.h"

int main() {
    Py_Initialize();
    initlib();
    printf("main: Calling test100000Times() in lib.so...\n");
    test100000Times();
    printf("main: Finished.\n");
    Py_Finalize();
    return 0;
}
```

编译过程：

```shell
cd pyx
cython lib.pyx
gcc -c lib.c main.c -I/usr/include/python2.7
gcc -L/usr/lib/python2.7 -L/usr/lib/python2.7/config -lpython2.7 -ldl -lm lib.o main.o -o main
```

得到可执行文件main。

### 测试

目录`~/workspace/cython`

测试python版的lib.py：

`time python py/lib.py`

结果大概是

```
Test in pure python, 100000 times:
Done, value= 1463.47950736

real    0m6.714s
user    0m6.600s
sys     0m0.060s
```

测试C中调用Cython：

`time pyx/main`

结果

```
main: Calling test100000Times() in lib.so...
Test in cython, 100000 times:
Done, value= 1463.47949219
main: Finished.

real    0m1.243s
user    0m1.190s
sys     0m0.040s
```

- - -

[Cython]: http://cython.org/
