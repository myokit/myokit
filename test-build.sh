#!/usr/bin/env bash
rm myokit.egg-info -rf
rm dist -rf
python -m build
mkdir dist/sdist
tar -xzvf dist/myokit-*.tar.gz -C dist/sdist --strip-components=1
unzip dist/myokit-*-none-any.whl -d dist/wheel
meld myokit dist/wheel/myokit
meld myokit dist/sdist/myokit
meld tests dist/sdist/tests
