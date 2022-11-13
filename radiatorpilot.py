import asyncio
import datetime
import os
import signal

import meross_iot
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager

if os.environ.get('MEROSS_EMAIL') is None or os.environ.get('MEROSS_PASSWORD') is None or os.environ.get('MEROSS_DEVICE_NAME') is  None:
    print('MEROSS_EMAIL or MEROSS_PASSWORD or MEROSS_DEVICE_NAME is missing') 
    quit()

EMAIL = os.environ.get('MEROSS_EMAIL') or "YOUR_MEROSS_CLOUD_EMAIL"
PASSWORD = os.environ.get('MEROSS_PASSWORD') or "YOUR_MEROSS_CLOUD_PASSWORD"
DEVICE_NAME = os.environ.get('MEROSS_DEVICE_NAME') 

PATH = "/dev/shm/radiator/"
MAX = "MAX"
MIN = "MIN"
ACTUAL = "ACTUAL"
STATE = "STATE"

MAXVAL="19.5"
MINVAL="19.0"
DEFAULTACTVAL="19.001\n"
DELAY=30

if not os.path.exists(PATH): 
    os.mkdir(PATH)
MAX_FILE =  open(os.path.join(PATH, MAX), 'w+')
MAX_FILE.write(str(MAXVAL))
MIN_FILE =  open(os.path.join(PATH, MIN), 'w+')
MIN_FILE.write(str(MINVAL))
ACTUAL_FILE =  open(os.path.join(PATH, ACTUAL), 'w+')
ACTUAL_FILE.write(str(DEFAULTACTVAL))
STATE_FILE =  open(os.path.join(PATH, STATE), 'w+')
STATE_FILE.write("OFF")

global statevalue
global Shutdown

Shutdown = 0
statevalue = 0

def handler(signum, frame):
    global Shutdown
    signame = signal.Signals(signum).name
    Shutdown = 1
    print(f'Signal handler called with signal {signame} ({signum})') 
    print(f'Wait {DELAY}s ... Shtudown in progress... ') 
    

async def main():
    # Setup the HTTP client API from user-password
        http_api_client = await MerossHttpClient.async_from_user_password(email=EMAIL, password=PASSWORD)

        # Setup and start the device manager
        manager = MerossManager(http_client=http_api_client)
        await manager.async_init()

        # Retrieve all the MSS310 devices that are registered on this account
        await manager.async_device_discovery()
        plugs = manager.find_devices(device_type="mss310",device_name=DEVICE_NAME)
        if len(plugs) < 1:
            print("No MSS310 plugs found...")
        else:  
            # Turn it on channel 0
            # Note that channel argument is optional for MSS310 as they only have one channel
            dev = plugs[0]

            # Update device status: this is needed only the very first time we play with this device (or if the
            #  connection goes down)
            await dev.async_update()

            try:
                
                statevalue = 0
                
                minstr = MIN_FILE.read()
                minvalue = float(minstr)
                print(str(datetime.datetime.now()) + " - MIN:"+str(minvalue), end = ' ')
                actstr = ACTUAL_FILE.read()
                actvalue = float(actstr)
                print("ACTUAL:"+str(actvalue))

                if actvalue<minvalue:
                    await dev.async_turn_on(channel=0)
                    statevalue=1
                    STATE_FILE.write("ON")
                    print(str(datetime.datetime.now()) +  f" Turning on {dev.name}...")
                else: 
                    await dev.async_turn_off(channel=0)
                    statevalue=0
                    STATE_FILE.write("OFF")
                    print(str(datetime.datetime.now()) +  f" Turning off {dev.name}...")
            except Exception as err:
                print(f"Unexpected err={err}, type={type(err)}")
            finally:
                await asyncio.sleep(DELAY)


            while Shutdown==0:

                try:
                    MIN_FILE.seek(0)
                    minstr = MIN_FILE.read()
                    minvalue = float(minstr)
                    print(str(datetime.datetime.now()) + " - MIN:"+str(minvalue), end = ' ')
                    MAX_FILE.seek(0)
                    maxstr = MAX_FILE.read()
                    maxvalue = float(maxstr)
                    print("MAX:"+str(maxvalue), end = ' ')
                    ACTUAL_FILE.seek(0)
                    actstr = ACTUAL_FILE.read()
                    actvalue = float(actstr)
                    print("ACTUAL:"+str(actvalue))

                    if not statevalue and actvalue <= minvalue:
                        await dev.async_turn_on(channel=0)
                        statevalue=1
                        STATE_FILE.write("ON")
                        print(str(datetime.datetime.now()) +  f" Turning on {dev.name}...")
                    elif statevalue and actvalue >= maxvalue: 
                        await dev.async_turn_off(channel=0)
                        statevalue=0
                        STATE_FILE.write("OFF")
                        print(str(datetime.datetime.now()) +  f" Turning off {dev.name}...")
                    
                except Exception as err:
                    print(f"Unexpected err={err}, type={type(err)}")
                finally:
                    await asyncio.sleep(DELAY)
            
            await dev.async_turn_off(channel=0)
            manager.close()
            await http_api_client.async_logout()
            print("Bye ! ")

signal.signal(signal.SIGINT, handler)



if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
    MAX_FILE.close()
    MIN_FILE.close()
    ACTUAL_FILE.close()
