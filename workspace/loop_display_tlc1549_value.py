import display_tlc1549_value
import time

while True:
    display_tlc1549_value.readValue()
    time.sleep(0.2)

