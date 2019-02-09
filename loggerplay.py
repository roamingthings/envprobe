import time

import board
import busio
import adafruit_bme280
import adafruit_gps

# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# OR create library object using our Bus SPI port
# spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
# bme_cs = digitalio.DigitalInOut(board.D10)
# bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, bme_cs)

# change this to match the location's pressure (hPa) at sea level
bme280.sea_level_pressure = 1013.25

# Define RX and TX pins for the board's serial port connected to the GPS.
# These are the defaults you should use for the GPS FeatherWing.
# For other boards set RX = GPS module TX, and TX = GPS module RX pins.
RX = board.RX
TX = board.TX

# Create a serial connection for the GPS connection using default speed and
# a slightly higher timeout (GPS modules typically update once a second).
uart = busio.UART(TX, RX, baudrate=9600, timeout=3000)

# Create a GPS module instance.
gps = adafruit_gps.GPS(uart, debug=False)

gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')

gps.send_command(b'PMTK220,1000')

last_print = time.monotonic()


def print_environment_values():
    print("Temperature: %0.1f C" % bme280.temperature)
    print("Humidity: %0.1f %%" % bme280.humidity)
    print("Pressure: %0.1f hPa" % bme280.pressure)
    print("Altitude = %0.2f meters" % bme280.altitude)


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


while True:
    # Make sure to call gps.update() every loop iteration and at least twice
    # as fast as data comes from the GPS unit (usually every second).
    # This returns a bool that's true if it parsed new data (you can ignore it
    # though if you don't care and instead look at the has_fix property).
    gps.update()

    current = time.monotonic()
    if current - last_print >= 1.0:
        last_print = current

        print('=' * 40)  # Print a separator line.
        print_environment_values()

        # Every second print out current location details if there's a fix.
        if not gps.has_fix:
            # Try again if we don't have a fix yet.
            print('Waiting for fix...')
        else:
            print_gps_fix()
