#
# Provides support for working with data in formats used by HEKA.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
from ._patchmaster import ( # noqa
    AmplifierFile,
    AmplifierMode,
    AmplifierSeries,
    AmplifierState,
    AmplifierStateRecord,
    CSlowRange,
    EndianAwareReader,
    Filter1Setting,
    Filter2Type,
    Group,
    NoSupportedDAChannelError,
    PatchMasterFile,
    PulsedFile,
    Segment,
    SegmentClass,
    SegmentIncrement,
    SegmentStorage,
    Series,
    Stimulus,
    StimulusChannel,
    StimulusFile,
    StimulusFilterSetting,
    Sweep,
    Trace,
    TreeNode,
)
from ._importer import PatchMasterImporter


# Importers
_importers = {
    'heka': PatchMasterImporter,
}


def importers():
    """ Returns a dict of all importers available in this module. """
    return dict(_importers)
# Exporters
# Expression writers
