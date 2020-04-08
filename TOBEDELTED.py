from myokit.formats.sbml import SBMLImporter, SBMLImporterOld

# Test Case I: Old importer
# import with old importer
oldImporter = SBMLImporterOld()
mOld = oldImporter.model('myokit/tests/data/formats/sbml/HodgkinHuxley.xml')

# convert old model to mmt file
mmtOld = mOld.code()
with open('myokit/tests/data/formats/sbml/HodgkinHuxleyOld.mmt', 'w') as f:
    f.write(mmtOld)

# Test Case II: New Importer
newImporter = SBMLImporter()
mNew = newImporter.model('myokit/tests/data/formats/sbml/HodgkinHuxley.xml')

# convert old model to mmt file
mmtNew = mNew.code()
with open('myokit/tests/data/formats/sbml/HodgkinHuxley.mmt', 'w') as f:
    f.write(mmtNew)
