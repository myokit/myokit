#!/usr/bin/env python2
#
# Method to run all mmt files in a directory (non-recursive)
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import gc
import os
import fnmatch
import traceback
import myokit
import matplotlib.pyplot as pl


def run(path, filename=None):
    """
    Run all the mmt files in a given directory `path`.

    If `filename` is given, only the file with that name from `path` is run.
    """
    # Get absolute path
    path = os.path.abspath(path)

    # Change to dir
    os.chdir(path)

    # Run all
    glob = '*.mmt'
    found = False
    for fn in fnmatch.filter(os.listdir(path), glob):
        # Real file?
        if filename is not None:
            if fn != filename:
                continue
            else:
                found = True

        # Load and run
        try:
            print('Loading ' + fn)
            m, p, x = myokit.load(os.path.join(path, fn))
            try:
                print('Running...')
                myokit.run(m, p, x)
            except Exception:
                print(traceback.format_exc())
        except Exception:
            print('Unable to load.')
            print(traceback.format_exc())
        try:
            pl.close('all')
        except Exception:
            pass

        # Tidy up
        del(m, p, x)
        gc.collect()
        print('-' * 70)

    if filename is not None and not found:
        print('Unable to find file: ' + str(filename))
    else:
        print('Done!')
