import uasyncio as asyncio
from machine import UART
from utime import sleep

# https://bigdanzblog.wordpress.com/2016/03/26/sim800l-gsmgprs-cellular-eval-board-first-look/

import logging
log = logging.getLogger("uasyncio")
uart = UART(1, 9600)
from machine import Pin

cmds = [{"send": "AT", "expect": [b"AT", b"OK"], "comment" : "just checking if everything is hooked up & running"},
        {"send": "AT+CPIN?", "expect": [b"AT+CPIN?", b"OK"], "comment":"ensure there's no pin set"},
        {"send": "AT+SAPBR=3,1,\"APN\",\"iot.1nce.net\"", "expect": [b'AT+SAPBR=3,1,"APN","iot.1nce.net"', b"OK"], "comment":"set apn" },
        {"send": "AT+SAPBR=1,1", "expect": [b'AT+SAPBR=1,1', b"OK"], "comment":"open bearer, connection id 1"},
        #{"send": "AT+httpinit\n", "expect": [b""]},
        #{"send": 'AT+httppara="URL","google.com"\n', "expect": [b""]}
        ]

reset_pin = Pin(17, Pin.OUT)


async def sender():
    print("resetting")
    reset_pin.value(0)
    await asyncio.sleep(1)
    reset_pin.value(1)
    await asyncio.sleep(5)

    sreader = asyncio.StreamReader(uart)
    swriter = asyncio.StreamWriter(uart, {})
    for cmd in cmds:
        print("sending %s" % cmd["send"])
        await swriter.awrite(cmd['send'] + '\n')
        for line in cmd['expect'].insert(0, ):
            while True:
                await asyncio.sleep(1)
                print("waiting for %s" % line)
                res = await sreader.readline()
                # skip empty lines / unsolicited output
                if res == b"\r\n" or res == b'Call Ready\r\n' or res ==b'+CPIN: READY\r\n' or res == b'SMS Ready\r\n':
                    print("garbage line %s" %res)
                    continue
                #TODO: regex...
                if res != line + b"\r\n":
                    print('Error: Recieved % s, expected %s' % (res, line))
                    # throw error
                else:
                    print("Success, received", res)
                    # dispatch result
                break;
        print("command %s excecuted successfully" % cmd["send"].replace('\r','').replace("\n", ''))
    print("all commands executed successfully")


loop = asyncio.get_event_loop()
loop.create_task(sender())
loop.run_forever()
