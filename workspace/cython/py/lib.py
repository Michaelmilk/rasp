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
    
