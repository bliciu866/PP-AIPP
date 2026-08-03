from pp_aipp.core import Kernel

kernel = Kernel()
kernel.start()
print(kernel.health())
kernel.stop()
