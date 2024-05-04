import asyncio
from door import Door

from test_helpers import run_async


async def test_move():
    """test moving up"""
    door = Door()
    revs = 2.5

    await door.open(revs)
    asyncio.sleep(2)
    await door.close(revs)
    asyncio.sleep(2)


async_tests = [test_move]
for test in async_tests:
    run_async(test, timeout=20)
