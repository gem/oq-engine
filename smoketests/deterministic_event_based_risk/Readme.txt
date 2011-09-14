In this demonstration, loss distribution and loss statistics are computed due to a single event. 

A hypothetical exposure model containing the economic value of 3276 assets (distributed across 1092 sites) and comprising 3 different building typologies (masonry, low-rise and mid-rise concrete buildings) is provided. In these calculations, a region that covers a smaller portion of the exposure model was defined, covering 423 assets (distributed throughout 141 sites). 
The vulnerability model uses peak ground acceleration and each vulnerability function is defined in a discrete way which means that a loss ratio and associated uncertainty is provided for a list of intensity measure levels. 

The rupture has a magnitude of 7.1 Mw and it is intended to represent the 1908 Messina historical earthquake and for the same event, 100 ground motion fields are produced to represent the aleatory variability (both inter- and intra-variability) in the ground motion. The spatial correlation in the ground motion variability is taken into account, as well as the correlation in the vulnerability functions (assumed as perfectly correlated).

A loss map with the mean loss and respective standard deviation per asset is computed, as well as the total mean loss and standard deviation. Scripts to parse the output and plot loss maps are available Ð more information is available at: https://github.com/gem/openquake/wiki/Using-OpenQuake-with-Cloud-Computing

This demo is expected to take about 4 minutes to complete using OATS. 