import spidev

spi = spidev.SpiDev()

def readValue():
    spi.open(0, 0)
    data = spi.readbytes(2)
    print "TLC1549 value:"
    value = ((data[0] & 0b11111111) << 2) + ((data[1] & 0b11000000) >> 6)
    print value
    spi.close()
    return value

if __name__ == "__main__":
	readValue()
