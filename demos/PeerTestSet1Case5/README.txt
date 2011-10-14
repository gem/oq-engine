Source model consisting of a single fault (PEER test "FAULT 1" model
The original data provided in the PEER Report ("Verification of Probabilistic Seismic Hazard Analysis Computer Programs", 
Patricia Thomas, Ivan Wong, Norman Abrahamson, Pacific Earthquake Engineering Research Center) are the following:
b value = -0.9
minimum magnitude = 5.0
maximum magnitude = 6.5
slip rate (m/yr) = 2e-3
rigidity (N/m2) = 3e10
fault length  (m) = 25*1e3
fault width (m) = 12*1e3
From the above data we can calculate the seismic moment rate (N*m/yr):
seismic moment rate = rigidity * fault length * fault width * slip rate
The test set 1 case 5 define the magnitude frequency distribution as truncated exponential with minimum magnitude = 5.0 and maximum magnitude = 6.5.
We can then compute the incremental a value using the formula given in Ward 1994 (eq. 10 pag. 1299) 
("A multidisciplinary approach to seismic hazard in Southern California", BSSA, Vol.84, No.5, pp.1293-1309, October 1994):
incremental a value = log10( (log(10) * (1.5 + b value) * seismic moment rate) / (10^((1.5 + b value) * maximum magnitude + 9.05)) )
from the incremental a value we can then derive the cumulative a value, using the following formula:
cumulative a value = incremental a value - log10(-b value * log(10))
the resulting cumulative a value is 3.1292
