Source model consisting of a single fault (PEER test "FAULT 1" model)
The original data provided in the PEER Report ("Verification of Probabilistic Seismic Hazard Analysis Computer Programs", 
Patricia Thomas, Ivan Wong, Norman Abrahamson, Pacific Earthquake Engineering Research Center) are the following:
b value = -0.9
slip rate (m/yr) = 2e-3
rigidity (N/m2) = 3e10
fault length  (m) = 25*1e3
fault width (m) = 12*1e3
From the above data we can calculate the seismic moment rate (N*m/yr):
seismic moment rate = rigidity * fault length * fault width * slip rate
For test set 1 case 2, the magnitude density function is assumed to be a delta function at M = 6.0.
We can then compute the corresponding occurrence rate, calculating first the incremental a value assuming M=6 as the only possible rupture. 
By imposing the following equality:
10^(a incremental + b value * M) * 10(1.5 * M + 9.05) = seismic moment rate
we can derive the following equation:
a incremental = log10(seismic moment rate) - (1.5 + b value) * M - 9.05
from the incremental a value we can then derive the cumulative a value, using the following formula:
cumulative a value = incremental a value - log10(-b value * log(10))
the resulting cumulative a value is 3.2828. By defining the magnitude frequency distribution of the fault to have Mmin=Mmax=M=6, 
we can define a delta function as requested by the test and with the appropriate occurrence rate.
