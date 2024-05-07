import supervisor
print("--------------booting---------------")
supervisor.runtime.autoreload = False  # CirPy 8 and above
print(f"{supervisor.runtime.autoreload=}")