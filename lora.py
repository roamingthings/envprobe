"""TinyLoRa with a Si7021 Sensor.
"""
import time
import busio
import digitalio
import board
import neopixel
import adafruit_bme280
import adafruit_gps
from adafruit_tinylora.adafruit_tinylora import TTN, TinyLoRa

# Board LED
led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT


def init_bme280():
    global bme280
    i2c = busio.I2C(board.SCL, board.SDA)
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
    bme280.sea_level_pressure = 1013.25


def init_lora():
    global lora
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

def init_gps():
    global gps
    RX = board.RX
    TX = board.TX
    uart = busio.UART(TX, RX, baudrate=9600, timeout=3000)
    gps = adafruit_gps.GPS(uart, debug=False)
    gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
    gps.send_command(b'PMTK220,1000')


def print_environment_values(temperature, humidity, pressure, altitude):
    print("Temperature: %0.1f C" % temperature)
    print("Humidity: %0.1f %%" % humidity)
    print("Pressure: %0.1f hPa" % pressure)
    print("Altitude: %0.2f meters" % altitude)


def print_gps_fix():
    # We have a fix! (gps.has_fix is true)
    # Print out details about the fix like location, date, etc.
    print('Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}'.format(
        gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
        gps.timestamp_utc.tm_mday,  # struct_time object that holds
        gps.timestamp_utc.tm_year,  # the fix time.  Note you might
        gps.timestamp_utc.tm_hour,  # not get all data like year, day,
        gps.timestamp_utc.tm_min,  # month!
        gps.timestamp_utc.tm_sec))
    print('Latitude: {} degrees'.format(gps.latitude))
    print('Longitude: {} degrees'.format(gps.longitude))
    print('Fix quality: {}'.format(gps.fix_quality))
    # Some attributes beyond latitude, longitude and timestamp are optional
    # and might not be present.  Check if they're None before trying to use!
    if gps.satellites is not None:
        print('# satellites: {}'.format(gps.satellites))
    if gps.altitude_m is not None:
        print('Altitude: {} meters'.format(gps.altitude_m))
    if gps.track_angle_deg is not None:
        print('Speed: {} knots'.format(gps.speed_knots))
    if gps.track_angle_deg is not None:
        print('Track angle: {} degrees'.format(gps.track_angle_deg))
    if gps.horizontal_dilution is not None:
        print('Horizontal dilution: {}'.format(gps.horizontal_dilution))
    if gps.height_geoid is not None:
        print('Height geo ID: {} meters'.format(gps.height_geoid))

# Configure the setup
PIXEL_PIN = board.NEOPIXEL   # pin that the NeoPixel is connected to
ORDER = neopixel.RGB   # pixel color channel order
CLEAR = (0, 0, 0)      # clear (or second color)

# Create the NeoPixel object
pixel = neopixel.NeoPixel(PIXEL_PIN, 1, pixel_order=ORDER)
pixel[0] = CLEAR

init_bme280()
init_gps()
init_lora()

# Data Packet to send to TTN
data = bytearray(32)

print("Starting main loop. It will take 30s for the first update to appear")
last_processed = time.monotonic()
while True:
    gps.update()

    current = time.monotonic()
    if current - last_processed >= 30.0:
        last_processed = current
        print("Processing...")
        temp_val = bme280.temperature
        humid_val = bme280.humidity
        pressure_val = bme280.pressure
        altitude_val = bme280.altitude
        print('=' * 40)  # Print a separator line.
        print_environment_values(temp_val, humid_val, pressure_val, altitude_val)

        time_val = 0
        latitude_val = 0
        longitude_val = 0
        gps_mon = 0
        gps_mday = 0
        gps_year = 0
        gps_hour = 0
        gps_min = 0
        gps_sec = 0
        if gps.has_fix:
            print_gps_fix()
            latitude_val = gps.latitude
            longitude_val = gps.longitude
            gps_mon = gps.timestamp_utc.tm_mon
            gps_mday = gps.timestamp_utc.tm_mday
            gps_year = gps.timestamp_utc.tm_year
            gps_hour = gps.timestamp_utc.tm_hour
            gps_min = gps.timestamp_utc.tm_min
            gps_sec = gps.timestamp_utc.tm_sec

        # Encode float as int
        temp_val = int(temp_val * 100)
        humid_val = int(humid_val * 100)
        pressure_val = int(pressure_val * 10)
        altitude_val = int(altitude_val * 100)
        latitude_val = int(latitude_val * 10000)
        longitude_val = int(longitude_val * 10000)

        # Encode payload as bytes
        data[0] = 0x01
        data[1] = (temp_val >> 8) & 0xff
        data[2] = temp_val & 0xff
        data[3] = (humid_val >> 8) & 0xff
        data[4] = humid_val & 0xff
        data[5] = (pressure_val >> 8) & 0xff
        data[6] = pressure_val & 0xff
        data[7] = (altitude_val >> 8) & 0xff
        data[8] = altitude_val & 0xff
        data[9] = gps_year & 0xff
        data[10] = gps_mon & 0xff
        data[11] = gps_mday & 0xff
        data[12] = gps_hour & 0xff
        data[13] = gps_min & 0xff
        data[14] = gps_sec & 0xff

        # Send data packet
        led.value = True
        lora.send_data(data, len(data), lora.frame_counter)
        print('Packet Sent')
        lora.frame_counter += 1
        led.value = False
