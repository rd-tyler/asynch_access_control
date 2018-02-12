#!/usr/bin/env python3.6

# stdlib
import sys
import json
import datetime as dt

# 3rd party
import curio  # https://github.com/dabeaz/curio
import curio_http

# Hardware
import BBb_GPIO # Modified from: https://github.com/rainierez/MatrixKeypad_Python/blob/master/matrix_keypad/BBb_GPIO.py
import Adafruit_CharLCD as LCD

# Specific functions and classes
kp = BBb_GPIO.keypad(columnCount = 3) # Keypad

# Global constants
GATE_CODE_URL = 'http://private-bbe140-sle1.apiary-mock.com/site/123/gatecodes'
SLEEP_TIME = 2 * 60 # In seconds 
SLEEP_TIMEDELTA = dt.timedelta(seconds=SLEEP_TIME)
MAX_CODE_LEN = 6

# Beaglebone Black pin configuration:
#lcd pin
lcd_rs = "P8_8"
lcd_en = "P8_10"
lcd_d4 = "P8_18"
lcd_d5 = "P8_16"
lcd_d6 = "P8_14"
lcd_d7 = "P8_12"
lcd_backlight = "" # Needs assignment

# LCD column and row config
lcd_columns = 16
lcd_rows = 2

# Initialize LCD
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

async def main():
    now = dt.datetime.now()
    while True:
        try:
            # Checks if SLEEP_TIME has elapsed 
            if dt.datetime.now() - now > SLEEP_TIMEDELTA: 
                now = dt.datetime.now()
                await get_codes()
            await get_inputs()
        except (KeyboardInterrupt, EOFError):
            print('Exiting Gracefully')
            break


async def get_inputs():
    # user_input = input("Please enter your gate code: ")
    # Not sure how this plays with async quite yet
    user_input = []
    print("Please enter your gate code:")
    # lcd.blink(True)
    # lcd.message("Gate Code:")
    try:
        init_digit = get_digit()
        user_input.append(init_digit) 
        # Once first input is detected waits for remaining inputs
        if len(user_input) > 0:
            while len(user_input) < MAX_CODE_LEN:
                temp_digit = get_digit()
                user_input.append(temp_digit)
                print(user_input)
                # lcd.message(user_input)
                sleep(1)
    except:
        # Moves on if no input is detected
        break

    try:
        user_code = int(user_input)
        codes = await load_codes()
        print(codes)
        # Checks if access code is in the access list
        if codes.get(user_code) is not None:
            if codes[user_code]['isActive']: # Checks if account is active
                print("Access Granted")
            else:
                print(codes[user_code]['message']) # Displays account message
        else:
            print("Access Denied")
    except ValueError:
        print("Gate code is not numeric")


async def load_codes():
    """
    Converts format from
    {'gateCodes': [{'gateCode': 654789,
                'isActive': True,
                'message': 'Hello, Larry. Access is granted!'},
               {'gateCode': 789456,
                'isActive': False,
                'message': 'Sorry, Sally, Your gate code has been suspended. '
                           'Please contact Customer Service at 888-555-1212.'},
               {'gateCode': 426486,
                'isActive': True,
                'message': 'Hello, Sam. Access is granted!'}]}
    => TO =>
    {
        654789: {
            'isActive': True,
            'message': 'Hello, Larry. Access is granted!'
        },
        789456: {
            'isActive': False,
            'message': 'Sorry, Sally, Your gate code has been suspended. Please contact Customer Service at 888-555-1212.'
        },
        426486: {
            'isActive': True,
            'message': 'Hello, Sam. Access is granted!'
        }
    }
    """
    with open('./codes.json', 'r') as fobj: # Creates local file object
        codes = json.loads(fobj.read()) # Reads local file object
    new_codes = {}
    # Changes format making Gate Code the unique ID
    for code in codes['gateCodes']:
        new_codes[code['gateCode']] = {
            'isActive': code['isActive'],
            'message': code['message']
        }
    return new_codes


async def get_codes():
    try:
        data = await fetchpage(GATE_CODE_URL)
        with open('./codes.json', 'w') as fobj:
            fobj.write(json.dumps(data))
    except Exception as e:
        print(e)
        raise


async def fetchpage(url):
    """ Async fetch page """
    # http://scribu.net/blog/asynchronous-http-requests-in-python-3.5.html
    async with curio_http.ClientSession() as session:
        response = await session.get(GATE_CODE_URL)
        return await response.json()

async def get_digit():
    digit = None
    while digit == None:
        digit = kp.getKey()
    return digit


if __name__ == '__main__':
    curio.run(main())