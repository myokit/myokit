#!/usr/bin/env python3
#
# Regenerates static test data
#
#
from shared import DIR_DATA

import myokit
import myokit.formats


def generate_all():
    """
    (Re)Generate all static test data.
    """
    generate_cellml_v1_parser_test_model()
    generate_cellml_v2_parser_test_model()
    generate_datablock_for_cv1d_test()
    generate_easyml_model()


def generate_cellml_v1_parser_test_model():
    """ Regenerate the CellML model used to test the v1 parser. """

    n = 'beeler-1977'
    m = myokit.load_model(DIR_DATA / f'{n}.mmt')
    e = myokit.formats.exporter('cellml1')
    e.model(DIR_DATA / 'generated' / f'{n}-cellml-v1.cellml', m)


def generate_cellml_v2_parser_test_model():
    """ Regenerate the CellML model used to test the v2 parser. """

    n = 'beeler-1977'
    m = myokit.load_model(DIR_DATA / f'{n}.mmt')
    e = myokit.formats.exporter('cellml2')
    e.model(DIR_DATA / 'generated' / f'{n}-cellml-v2.cellml', m)


def generate_datablock_for_cv1d_test():
    m, p, _ = myokit.load(DIR_DATA / 'beeler-1977.mmt')
    s = myokit.Simulation1d(m, p, 64)
    d = s.run(500, log=['engine.time', 'membrane.V', 'engine.pace'])
    b = d.block1d()
    b.save(DIR_DATA / 'generated' / 'cv1d.zip')
    print(myokit.float.str(b.cv('membrane.V')))


def generate_easyml_model():
    """ Regenerate the EasyML model used to check export. """

    n = 'beeler-1977-for-export-testing'
    m = myokit.load_model(DIR_DATA / f'{n}.mmt')
    e = myokit.formats.exporter('easyml')
    e.model(DIR_DATA / 'generated' / f'{n}.model', m)


if __name__ == '__main__':
    generate_all()
