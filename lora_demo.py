"""Simple program to demonstrate the issue with payloads larger than 7 bytes..
"""
import time
import busio
import digitalio
import board
from adafruit_tinylora.adafruit_tinylora import TTN, TinyLoRa

# Create library object using our bus SPI port for radio
spi = busio.SPI(board.SCK, MISO=board.MISO, MOSI=board.MOSI)
# RFM9x Breakout Pinouts
cs = digitalio.DigitalInOut(board.D6)
irq = digitalio.DigitalInOut(board.D5)
# TTN Device Address, 4 Bytes, MSB
devaddr = bytearray([0x26, 0x01, 0x14, 0xE1])
# TTN Network Key, 16 Bytes, MSB
nwkey = bytearray([0xAF, 0x6E, 0xE8, 0xC4, 0x20, 0x42, 0x62, 0x86,
                   0x96, 0xFB, 0xFB, 0xF7, 0x74, 0x00, 0xA7, 0xA1])
# TTN Application Key, 16 Bytess, MSB
app = bytearray([0x7F, 0x06, 0x6A, 0xF1, 0xE2, 0xD9, 0xDB, 0x62,
                 0x53, 0x39, 0x53, 0xA7, 0x90, 0x9D, 0x60, 0xC2])
ttn_config = TTN(devaddr, nwkey, app, country='EU')
lora = TinyLoRa(spi, cs, irq, ttn_config)

# Data Packet to send to TTN
# 7 bytes of Payload are working
shortPayload = bytearray(7)
# 8 bytes and more won't
longPayload = bytearray(8)

while True:
        print('Sending short packet...')
        lora.send_data(shortPayload, len(shortPayload), lora.frame_counter)
        lora.frame_counter += 1
        print('Sending long packet...')
        lora.send_data(longPayload, len(longPayload), lora.frame_counter)
        lora.frame_counter += 1
        time.sleep(5)
