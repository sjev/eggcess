# Run tests on device
# each module should have a test function that runs the tests
print("running tests")

ALL_TESTS = ["timing", "uln2003"]
SERVER_TESTS = ["webserver"]

for name in SERVER_TESTS:
    print(f"---------testing {name}------------")
    module = __import__(name)
    module.test()
