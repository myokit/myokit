#
# Provides an export to OpenCL
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from ._exporter import OpenCLExporter, OpenCLRLExporter
from ._ewriter import OpenCLExpressionWriter
from myokit.formats import ansic


# Importers
# Exporters
_exporters = {
    'opencl': OpenCLExporter,
    'opencl-rl': OpenCLRLExporter,
}


def exporters():
    """
    Returns a dict of all exporters available in this module.
    """
    return dict(_exporters)


# Expression writers
_ewriters = {
    'opencl': OpenCLExpressionWriter,
}


def ewriters():
    """
    Returns a dict of all expression writers available in this module.
    """
    return dict(_ewriters)


# Keywords
keywords = list(ansic.keywords)
keywords.extend([
    # Data types
    'bool',
    'char',
    'uchar',
    'short',
    'ushort',
    'int',
    'uint',
    'long',
    'ulong',
    'float',
    'half',
    'size_t',
    'ptrdiff_t',
    'intptr_t',
    'uintptr_t',
    'void',
    'unsigned',
    # Vector data types
    'char2', 'char4', 'char8', 'char16',
    'uchar2', 'uchar4', 'uchar8', 'uchar16',
    'short2', 'short4', 'short8', 'short16',
    'ushort2', 'ushort4', 'ushort8', 'ushort16',
    'int2', 'int4', 'int8', 'int16',
    'uint2', 'uint4', 'uint8', 'uint16',
    'long2', 'long4', 'long8', 'long16',
    'ulong2', 'ulong4', 'ulong8', 'ulong16',
    'float2', 'float4', 'float8', 'float16',
    # Other data types
    'image2d_t',
    'image3d_t',
    'sampler_t',
    'event_t',
    # Reserved data types
    'bool2', 'bool4', 'bool8', 'bool16',
    'double',
    'double2', 'double4', 'double8', 'double16',
    'half2', 'half4', 'half8', 'half16',
    'quad',
    'quad2', 'quad4', 'quad8', 'quad16',
    'complex half',
    'complex half2', 'complex half4', 'complex half8', 'complex half16',
    'imaginary half',
    'imaginary half2', 'imaginary half4', 'imaginary half8',
    'imaginary half16',
    'complex float',
    'complex float2', 'complex float4', 'complex float8', 'complex float16',
    'imaginary float',
    'imaginary float2', 'imaginary float4', 'imaginary float8',
    'imaginary float16',
    'complex double',
    'complex double2', 'complex double4', 'complex double8',
    'complex double16',
    'imaginary double',
    'imaginary double2', 'imaginary double4', 'imaginary double8',
    'imaginary double16',
    'complex quad',
    'complex quad2', 'complex quad4', 'complex quad8', 'complex quad16',
    'imaginary quad',
    'imaginary quad2', 'imaginary quad4', 'imaginary quad8',
    'imaginary quad16',
    'float2x2', 'float2x4', 'float2x8', 'float2x16',
    'float4x2', 'float4x4', 'float4x8', 'float4x16',
    'float8x2', 'float8x4', 'float8x8', 'float8x16',
    'float16x2', 'float16x4', 'float16x8', 'float16x16',
    'double2x2', 'double2x4', 'double2x8', 'double2x16',
    'double4x2', 'double4x4', 'double4x8', 'double4x16',
    'double8x2', 'double8x4', 'double8x8', 'double8x16',
    'double16x2', 'double16x4', 'double16x8', 'double16x16',
    'long double',
    'long double2', 'long double4', 'long double8', 'long double16',
    'long long',
    'long long2', 'long long4', 'long long8', 'long long16',
    'unsigned long long',
    'ulong long',
    'ulong long2', 'ulong long4', 'ulong long8', 'ulong long16',
    # Address space qualifiers
    '__global',
    '__local',
    '__constant',
    '__private',
    # Image access qualifiers
    '__read_only',
    '__write_only',
    # Function qualifiers
    '__kernel',
    '__attribute__',
    # ^ These don't really need to be here, since variables names never start
    # on an underscore in myokit.
    # Work-item functions
    'get_work_dim',
    'get_global_size',
    'get_global_id',
    'get_local_size',
    'get_local_id',
    'get_num_groups',
    'get_group_id',
    # Math functions
    'acosh',
    'acospi',
    'asin',
    'asinh',
    'asinpi',
    'atan',
    'atan2',
    'atanh',
    'atanpi',
    'atan2pi',
    'cbrt',
    'ceil',
    'copysign',
    'cos',
    'cosh',
    'cospi',
    'erfc',
    'erf',
    'exp',
    'exp2',
    'exp10',
    'expm1',
    'fabs',
    'fdim',
    'floor',
    'fma',
    'fmax',
    'fmin',
    'fmod',
    'fract',
    'frexp',
    'hypot',
    'ilogb',
    'ldexp',
    'lgamma',
    'lgamma_r',
    'log',
    'log2',
    'log10',
    'log1p',
    'logb',
    'mad',
    'modf',
    'nan',
    'nextafter',
    'pow',
    'pown',
    'powr',
    'remainder',
    'remquo',
    'rint',
    'rootn',
    'round',
    'rsqrt',
    'sin',
    'sincos',
    'sinh',
    'sinpi',
    'sqrt',
    'tan',
    'tanh',
    'tanpi',
    'tgamma',
    'trunc',
    # Special math functions
    'half_cos',
    'half_divide',
    'half_exp',
    'half_exp2',
    'half_exp10',
    'half_log',
    'half_log2',
    'half_log10',
    'half_powr',
    'half_recip',
    'half_rsqrt',
    'half_sin',
    'half_sqrt',
    'half_tan',
    'native_cos',
    'native_divide',
    'native_exp',
    'native_exp2',
    'native_exp10',
    'native_log',
    'native_log2',
    'native_log10',
    'native_powr',
    'native_recip',
    'native_rsqrt',
    'native_sin',
    'native_sqrt',
    'native_tan',
    # Math constants
    'MAXFLOAT',
    'HUGE_VALF',
    'INFINITY',
    'NAN',
    # Math macros
    'FLT_DIG',
    'FLT_MANT_DIG',
    'FLT_MAX_10_EXP',
    'FLT_MAX_EXP',
    'FLT_MIN_10_EXP',
    'FLT_MIN_EXP',
    'FLT_RADIX',
    'FLT_MAX',
    'FLT_MIN',
    'FLT_EPSILON',
    # Integer functions
    'abs',
    'abs_diff',
    'add_sat',
    'hadd',
    'rhadd',
    'clz',
    'mad_hi',
    'mad_sat',
    'max',
    'min',
    'mul_hi',
    'rotate',
    'sub_sat',
    'upsample',
    'mad24',
    'mul24',
    # Integer macros
    'CHAR_BIT',
    'CHAR_MAX',
    'CHAR_MIN',
    'INT_MAX',
    'INT_MIN',
    'LONG_MAX',
    'LONG_MIN',
    'SCHAR_MAX',
    'SCHAR_MIN',
    'SHRT_MAX',
    'SHRT_MIN',
    'UCHAR_MAX',
    'USHRT_MAX',
    'UINT_MAX',
    'ULONG_MAX',
    # Common functions
    'clamp',
    'degrees',
    'max',
    'min',
    'mix',
    'radians',
    'step',
    'smoothstep',
    'sign',
    # Geometric functions
    'cross',
    'dot',
    'distance',
    'length',
    'normalize',
    'fast_distance',
    'fast_length',
    'fast_normalize',
    # Relational functions
    'isequal',
    'isnotequal',
    'isgreater',
    'isgreaterequal',
    'isless',
    'islessequal',
    'islessgreater',
    'isfinite',
    'isinf',
    'isnan',
    'isnormal',
    'isordered',
    'isunordered',
    'signbit',
    'any',
    'all',
    'bitselect',
    'select',
    # Vector data
    'vload2', 'vload4', 'vload8', 'vload16',
    'vstore2', 'vstore4', 'vstore8', 'vstore16',
    'vload_half',
    'vload_half2', 'vload_half4', 'vload_half8', 'vload_half16',
    'vstore_half',
    'vstore_half2', 'vstore_half4', 'vstore_half8', 'vstore_half16',
    # Other
    'union',
    'atomic_cmpxchg',
    #TODO
    # There's still more :)
])
