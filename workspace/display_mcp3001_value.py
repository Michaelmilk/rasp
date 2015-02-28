import spidev

def readValue():
    spi = spidev.SpiDev()
    spi.open(0, 0)
    data = spi.readbytes(2)
    print "MCP3001 value:"
    print ((data[0] & 0b00011111) << 5) + ((data[1] & 0b11111000) >> 3)
    spi.close()

if __name__ == "__main__":
	readValue()
