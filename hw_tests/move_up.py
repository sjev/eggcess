""" turn the motor given number of revolutions, measure distance traveled """

import asyncio
from door import Door, STATE_CLOSED


async def move():
    """test moving up"""
    door = Door(save_state=False)
    door.state = STATE_CLOSED
    revs = 10
    print(f"Moving up {revs} revolutions")

    await door.open(revs)


asyncio.run(move())
