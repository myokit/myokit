## When exporting

./myokit/formats/ansic/template/euler.c:    print(tab + v(var) + ' = ' + myokit.float.str(var.initial_value(True)) + ';')
./myokit/formats/easyml/_exporter.py:                        + myokit.float.str(v.initial_value(True)) + eos)

Why only these two? Does it work in the others?


./myokit/formats/opencl/template/cable.c:    print(tab*2 + '*s = ' + myokit.float.str(v.initial_value(True)) + '; s++; // ' + str(v.qname()))

./myokit/formats/diffsl/_exporter.py:            rhs = e.ex(v.initial_value())

./myokit/lib/hh.py:            [v.initial_value(True) for v in self._states])
./myokit/lib/markov.py:            [v.initial_value(True) for v in self._states])

./myokit/_sim/cmodel.h:    print(tab + v(var) + ' = ' + myokit.float.str(var.initial_value(True)) + ';')

./myokit/_model_api.py:                        [e.var() for e in var.initial_value().references()])
./myokit/_model_api.py:                state_map[var].initial_value().clone(subst=lhs_map))
./myokit/_model_api.py:            value = var.initial_value()
./myokit/_model_api.py:                value = self.initial_value(True)
./myokit/_model_api.py:            value = self.initial_value()
./myokit/_model_api.py:        return self.initial_value(as_float=True)


