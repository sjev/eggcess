""" test helper functions"""
import asyncio


def run(fcn):
    """run a test function"""
    print(f"-------------- {fcn.__name__} --------------")
    try:
        fcn()
        print("Test passed")
    except Exception as e:
        print(f"Test ***FAILED***: {e}")


async def run_with_wait_for(coro, timeout):
    """Helper coroutine to run another coroutine with a timeout using asyncio.wait_for."""
    if timeout is not None:
        await asyncio.wait_for(coro, timeout)
    else:
        await coro


def run_async(coro, timeout: float | None = None):
    """Run an async test function with an optional timeout."""
    print(f"--------------- {coro.__name__} ---------------")
    try:
        asyncio.run(run_with_wait_for(coro(), timeout))
        print("Test passed")
    except asyncio.TimeoutError:
        print("Test ***CANCELED*** due to timeout.")
    except Exception as e:
        print(f"Test ***FAILED***: {type(e).__name__}: {e}")
