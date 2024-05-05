# Run tests on device
# each module should have a test function that runs the tests
print("running tests")

for name in ["timing", "uln2003"]:
    print(f"---------testing {name}------------")
    module = __import__(name)
    module.test()
