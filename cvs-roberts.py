#!/usr/bin/env python3
import myokit
m = myokit.parse_model('''
[[model]]
desc: "Roberts" example from CVODE(s)
rob.y1 = 1
rob.y2 = 0
rob.y3 = 0

[engine]
time = 0
    bind time

[rob]
p1 = 0.04
p2 = 1e4
p3 = 3e7
dot(y1) = -p1 * y1 + p2 * y2 * y3
dot(y2) = +p1 * y1 - p2 * y2 * y3 - p3 * y2^2
dot(y3) = p3 * y2^2
''')

y1, y2, y3 = (m.get(x) for x in ('rob.y1', 'rob.y2', 'rob.y3'))
dy1, dy2, dy3 = (x.lhs() for x in (y1, y2, y3))
ny1, ny2, ny3 = (myokit.Name(x) for x in (y1, y2, y3))

p1, p2, p3 = (m.get(x) for x in ('rob.p1', 'rob.p2', 'rob.p3'))
np1, np2, np3 = (x.lhs() for x in (p1, p2, p3))

print('Jacobian')
print(y1.rhs().partial_derivative(ny1))
print(y1.rhs().partial_derivative(ny2))
print(y1.rhs().partial_derivative(ny3))
print()
print(y2.rhs().partial_derivative(ny1))
print(y2.rhs().partial_derivative(ny2))
print(y2.rhs().partial_derivative(ny3))
print()
print(y3.rhs().partial_derivative(ny1))
print(y3.rhs().partial_derivative(ny2))
print(y3.rhs().partial_derivative(ny3))
print()
print()
print('Sensitivity equations')
print(y1.rhs().partial_derivative(np1))
print(y2.rhs().partial_derivative(np1))
print(y3.rhs().partial_derivative(np1))
print()
print(y1.rhs().partial_derivative(np2))
print(y2.rhs().partial_derivative(np2))
print(y3.rhs().partial_derivative(np2))
print()
print(y1.rhs().partial_derivative(np3))
print(y2.rhs().partial_derivative(np3))
print(y3.rhs().partial_derivative(np3))

