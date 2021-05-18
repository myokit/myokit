#!/usr/bin/env python3
import myokit

print(myokit.OpenCL.test_extension_on_current_platform('cl_khr_fp64'))

print('<raw>')
print(myokit.OpenCL.test_extension_on_current_platform('cl_khr_fp64', True))
print('</raw>')

print('Single:')
m, p, _ = myokit.load('example')
s = myokit.SimulationOpenCL(m, p, ncells=2)
s.run(1)

print('Double:')
s = myokit.SimulationOpenCL(m, p, ncells=2, precision=myokit.DOUBLE_PRECISION)
s.run(1)
