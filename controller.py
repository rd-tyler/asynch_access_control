#!/usr/bin/env python3.6

# stdlib
import sys
import json
import datetime as dt

# 3rd party
import curio  # https://github.com/dabeaz/curio
import curio_http
import BBb_GPIO # Modified from: https://github.com/rainierez/MatrixKeypad_Python/blob/master/matrix_keypad/BBb_GPIO.py

# SPecific functions and classes
kp = BBb_GPIO.keypad(columnCount = 3) # Keypad

# Global constants
GATE_CODE_URL = 'http://private-bbe140-sle1.apiary-mock.com/site/123/gatecodes'
SLEEP_TIME = 2 * 60 # In seconds 
SLEEP_TIMEDELTA = dt.timedelta(seconds=SLEEP_TIME)


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
    for i in range(5):
        temp_digit = get_digit()    
        user_input.append(temp_digit)
        print(user_input)

    try:
        user_code = int(user_input) # Makes
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