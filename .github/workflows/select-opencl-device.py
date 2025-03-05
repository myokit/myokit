#!/usr/bin/env python3
#
# Select the best opencl device for testing: modifies myokit.ini !
#
import myokit


if myokit.OpenCL.available():

    # Search for a device with float capabilities
    best = second_best = None
    for platform in myokit.OpenCL.info().platforms:
        for device in platform.devices:
            if platform.has_extension('cl_khr_fp64'):
                if platform.has_extension('cl_khr_int64_base_atomics'):
                    best = platform.name, device.name
                    break
                elif second_best is None:
                    second_best = platform.name, device.name
            break

    if best is not None:
        print('Selected OpenCL device: ' + best[1])
        myokit.OpenCL.save_selection(*best)
    elif second_best is not None:
        print('Selected OpenCL device (2nd best): ' + second_best[1])
        myokit.OpenCL.save_selection(*second_best)

else:
    print('No OpenCL support detected.')
