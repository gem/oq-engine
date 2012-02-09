"""
A Magnitude Frequency Distribution (MFD) is a function that describes the rate
(per year) of earthquakes across all magnitudes.

Package `mfd` contains the basic class for MFD --
:class:`nhe.mfd.base.BaseMFD`, and two actual implementations:
:class:`nhe.mfd.evenly_discretized.EvenlyDiscretizedMFD`
and :class:`nhe.mfd.truncated_gr.TruncatedGRMFD`.
"""
from nhe.mfd.evenly_discretized import EvenlyDiscretizedMFD
from nhe.mfd.truncated_gr import TruncatedGRMFD
