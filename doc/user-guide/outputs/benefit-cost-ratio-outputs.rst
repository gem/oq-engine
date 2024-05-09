Benefit-Cost Ratio Outputs
==========================

Retrofitting benefit/cost ratio maps
------------------------------------

Ratio maps from the Retrofitting Benefit/Cost Ratio calculator require loss exceedance curves, which can be calculated 
using the Classical Probabilistic Risk calculator. For this reason, the parameters ``sourceModelTreePath`` and ``gsimTreePath`` 
are also included in this NRML schema, so the whole calculation process can be traced back. The results for each asset 
are stored as depicted in the table below.

Example benefit-cost ratio map output

+---------+---------+---------------+------------------+---------------------+---------+
| **lon** | **lat** | **asset_ref** | **aal_original** | **aal_retrofitted** | **bcr** |
+=========+=========+===============+==================+=====================+=========+
| 80.0888 | 28.8612 | a1846         | 966,606          | 53,037              | 1.72    |
+---------+---------+---------------+------------------+---------------------+---------+
| 80.0888 | 28.8612 | a4119         | 225,788          | 26,639              | 1.46    |
+---------+---------+---------------+------------------+---------------------+---------+
| 80.0888 | 28.8612 | a6444         | 444,595          | 16,953              | 1.33    |
+---------+---------+---------------+------------------+---------------------+---------+
| 80.0888 | 28.8612 | a8717         | 106,907          | 10,086              | 0.39    |
+---------+---------+---------------+------------------+---------------------+---------+
| 80.0888 | 28.9362 | a1784         | 964,381          | 53,008              | 1.92    |
+---------+---------+---------------+------------------+---------------------+---------+
| 80.0888 | 28.9362 | a4057         | 225,192          | 26,597              | 1.64    |
+---------+---------+---------------+------------------+---------------------+---------+
| 80.0888 | 28.9362 | a6382         | 443,388          | 16,953              | 1.49    |
+---------+---------+---------------+------------------+---------------------+---------+
| 80.0888 | 28.9362 | a8655         | 106,673          | 10,081              | 0.44    |
+---------+---------+---------------+------------------+---------------------+---------+
| 80.1292 | 29.0375 | a2250         | 1,109,310        | 60,989              | 2.08    |
+---------+---------+---------------+------------------+---------------------+---------+
| 80.1292 | 29.0375 | a4523         | 2,785,790        | 329,083             | 1.78    |
+---------+---------+---------------+------------------+---------------------+---------+
| ...     | ...     | ...           | ...              | ...                 | ...     |
+---------+---------+---------------+------------------+---------------------+---------+

- ``interestRate``: this parameter represents the interest rate used in the time-value of money calculations
- ``assetLifeExpectancy``: this parameter specifies the life expectancy (or design life) of the assets considered for the calculations
- ``node``: this schema follows the same ``node`` structure already presented for the loss maps, however, instead of losses for each asset, the benefit/cost ratio (``ratio``), the average annual loss considering the original vulnerability (``aalOrig``) and the average annual loss for the retrofitted (``aalRetr``) configuration of the assets are provided.