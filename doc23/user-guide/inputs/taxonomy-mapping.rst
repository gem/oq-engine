Taxonomy Mapping
================

In an ideal world, for every building type represented in the exposure model, there would be a unique matching function 
in the vulnerability or fragility models. However, often it may not be possible to have a one-to-one mapping of the 
taxonomy strings in the exposure and those in the vulnerability or fragility models. For cases where the exposure model 
has richer detail, many taxonomy strings in the exposure would need to be mapped onto a single vulnerability or fragility 
function. In other cases where building classes in the exposure are more generic and the fragility or vulnerability 
functions are available for more specific building types, a modeller may wish to assign more than one vulnerability or 
fragility function to the same building type in the exposure with different weights.

We may encode such information into a *taxonomy_mapping.csv* file like the following:

+--------------+----------------+
| **taxonomy** | **conversion** |
+==============+================+
|     Wood     |  Wood Type A   |
+--------------+----------------+
|     Wood     |  Wood Type B   |
+--------------+----------------+
|     Wood     |  Wood Type C   |
+--------------+----------------+

Using an external file is convenient, because we can avoid changing the original exposure. If in the future we will be 
able to get specific risk functions, then we will just remove the taxonomy mapping. This usage of the taxonomy mapping 
(use proxies for missing risk functions) is pretty useful, but there is also another usage which is even more interesting.

Consider a situation where there are doubts about the precise composition of the exposure. For instance we may know than 
in a given geographic region 20% of the building of type “Wood” are of “Wood Type A”, 30% of “Wood Type B” and 50% of 
“Wood Type C”, corresponding to different risk functions, but do not know building per building what it its precise 
taxonomy, so we just use a generic “Wood” taxonomy in the exposure. We may encode the weight information into a 
*taxonomy_mapping.csv* file like the following:

+--------------+----------------+------------+
| **taxonomy** | **conversion** | **weight** |
+==============+================+============+
|     Wood     |  Wood Type A   |    0.2     |
+--------------+----------------+------------+
|     Wood     |  Wood Type B   |    0.3     |
+--------------+----------------+------------+
|     Wood     |  Wood Type C   |    0.5     |
+--------------+----------------+------------+

The engine will read this mapping file and when performing the risk calculation will use all three kinds of risk functions 
to compute a single result with a weighted mean algorithm. The sums of the weights must be 1 for each exposure taxonomy, 
otherwise the engine will raise an error. In this case the taxonomy mapping file works like a risk logic tree.

Internally both the first usage and the second usage are treated in the same way, since the first usage is a special case 
of the second when all the weights are equal to 1.