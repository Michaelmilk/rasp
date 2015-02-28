import spidev

def readValue():
    spi = spidev.SpiDev()
    spi.open(0, 0)
    data = spi.readbytes(2)
    print "TLC1549 value:"
    print ((data[0] & 0b11111111) << 2) + ((data[1] & 0b11000000) >> 6)
    spi.close()

if __name__ == "__main__":
	readValue()
