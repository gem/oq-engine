"""
A Magnitude Frequency Distribution (MFD) is a function that describes the rate
(per year) of earthquakes across all magnitudes.

Package `mfd` contains the basic class for MFD --
:class:`nhe.mfd.base.BaseMFD`, and two actual implementations:
:class:`nhe.mfd.evenly_discretized.EvenlyDiscretized`
and :class:`nhe.mfd.truncated_gr.TruncatedGR`.
"""
from nhe.mfd.base import MFDError
from nhe.mfd.evenly_discretized import EvenlyDiscretized
from nhe.mfd.truncated_gr import TruncatedGR
