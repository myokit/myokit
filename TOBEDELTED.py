from myokit.formats.sbml import SBMLImporter


# Test Case I: New Importer
newImporter = SBMLImporter()
mNew = newImporter.model('myokit/tests/data/formats/sbml/HodgkinHuxley.xml')

# convert old model to mmt file
mmtNew = mNew.code()
with open('myokit/tests/data/formats/sbml/HodgkinHuxley.mmt', 'w') as f:
    f.write(mmtNew)
