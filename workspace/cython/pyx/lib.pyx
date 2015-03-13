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

