import time
import spidev

spi = spidev.SpiDev()

def readValue():
    spi.open(0, 0)
    data = spi.readbytes(2)
    val = ((data[0] & 0b11111111) << 2) + ((data[1] & 0b11000000) >> 6)
    spi.close()
    return val

while True:
    val = readValue()
    if val == 0:
        print "val=", val
    else:
        print "val=", val, " r=", 1024.0 * 510.0 / val - 510
    time.sleep(0.005)
