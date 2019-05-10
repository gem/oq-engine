applyToSources with multiple sources
====================================

============== ===================
checksum32     3,100,344,271      
date           2019-05-10T05:07:55
engine_version 3.5.0-gitbaeb4c1e35
============== ===================

num_sites = 1, num_levels = 1, num_rlzs = 9

Parameters
----------
=============================== ===================================================================================================================
calculation_mode                'preclassical'                                                                                                     
number_of_logic_tree_samples    0                                                                                                                  
maximum_distance                {'default': 30.0, 'Active Shallow Crust': 30.0, 'Subduction Interface': 100.0, 'Stable Continental Interior': 30.0}
investigation_time              1.0                                                                                                                
ses_per_logic_tree_path         1                                                                                                                  
truncation_level                None                                                                                                               
rupture_mesh_spacing            5.0                                                                                                                
complex_fault_mesh_spacing      50.0                                                                                                               
width_of_mfd_bin                0.5                                                                                                                
area_source_discretization      50.0                                                                                                               
ground_motion_correlation_model None                                                                                                               
minimum_intensity               {}                                                                                                                 
random_seed                     42                                                                                                                 
master_seed                     0                                                                                                                  
ses_seed                        42                                                                                                                 
=============================== ===================================================================================================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============ ======= =============== ================
smlt_path    weight  gsim_logic_tree num_realizations
============ ======= =============== ================
b1_b231_b361 0.20250 trivial(0,0,1)  1               
b1_b231_b362 0.12375 trivial(0,0,1)  1               
b1_b231_b363 0.12375 trivial(0,0,1)  1               
b1_b232_b361 0.12375 trivial(0,0,1)  1               
b1_b232_b362 0.07563 trivial(0,0,1)  1               
b1_b232_b363 0.07563 trivial(0,0,1)  1               
b1_b233_b361 0.12375 trivial(0,0,1)  1               
b1_b233_b362 0.07563 trivial(0,0,1)  1               
b1_b233_b363 0.07563 trivial(0,0,1)  1               
============ ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
3      '[SadighEtAl1997]' rrup      vs30       mag rake  
4      '[SadighEtAl1997]' rrup      vs30       mag rake  
5      '[SadighEtAl1997]' rrup      vs30       mag rake  
6      '[SadighEtAl1997]' rrup      vs30       mag rake  
7      '[SadighEtAl1997]' rrup      vs30       mag rake  
8      '[SadighEtAl1997]' rrup      vs30       mag rake  
9      '[SadighEtAl1997]' rrup      vs30       mag rake  
10     '[SadighEtAl1997]' rrup      vs30       mag rake  
11     '[SadighEtAl1997]' rrup      vs30       mag rake  
12     '[SadighEtAl1997]' rrup      vs30       mag rake  
13     '[SadighEtAl1997]' rrup      vs30       mag rake  
14     '[SadighEtAl1997]' rrup      vs30       mag rake  
15     '[SadighEtAl1997]' rrup      vs30       mag rake  
16     '[SadighEtAl1997]' rrup      vs30       mag rake  
17     '[SadighEtAl1997]' rrup      vs30       mag rake  
18     '[SadighEtAl1997]' rrup      vs30       mag rake  
19     '[SadighEtAl1997]' rrup      vs30       mag rake  
20     '[SadighEtAl1997]' rrup      vs30       mag rake  
21     '[SadighEtAl1997]' rrup      vs30       mag rake  
22     '[SadighEtAl1997]' rrup      vs30       mag rake  
23     '[SadighEtAl1997]' rrup      vs30       mag rake  
24     '[SadighEtAl1997]' rrup      vs30       mag rake  
25     '[SadighEtAl1997]' rrup      vs30       mag rake  
26     '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=9)
  1,'[SadighEtAl1997]': [0]
  4,'[SadighEtAl1997]': [1]
  7,'[SadighEtAl1997]': [2]
  10,'[SadighEtAl1997]': [3]
  13,'[SadighEtAl1997]': [4]
  16,'[SadighEtAl1997]': [5]
  19,'[SadighEtAl1997]': [6]
  22,'[SadighEtAl1997]': [7]
  25,'[SadighEtAl1997]': [8]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 1      Subduction Interface 633          633         
source_model.xml 4      Subduction Interface 633          633         
source_model.xml 7      Subduction Interface 633          633         
source_model.xml 10     Subduction Interface 633          633         
source_model.xml 13     Subduction Interface 633          633         
source_model.xml 16     Subduction Interface 633          633         
source_model.xml 19     Subduction Interface 633          633         
source_model.xml 22     Subduction Interface 633          633         
source_model.xml 25     Subduction Interface 633          633         
================ ====== ==================== ============ ============

============= ======
#TRT models   9     
#eff_ruptures 5,697 
#tot_ruptures 72,279
#tot_weight   79,658
============= ======

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
1      1         C    8     107   633          0.00768   1.00000   2,532 
10     1         C    629   728   633          0.00757   1.00000   2,532 
19     1         C    1,250 1,349 633          0.00721   1.00000   2,532 
16     1         C    1,043 1,142 633          0.00574   1.00000   2,532 
4      1         C    215   314   633          0.00516   1.00000   2,532 
13     1         C    836   935   633          0.00508   1.00000   2,532 
22     1         C    1,457 1,556 633          0.00452   1.00000   2,532 
25     1         C    1,664 1,763 633          0.00335   1.00000   2,532 
7      1         C    422   521   633          0.00310   1.00000   2,532 
26     8         A    1,853 1,863 8            0.0       0.0       0.0   
26     7         A    1,842 1,853 12           0.0       0.0       0.0   
26     6         A    1,830 1,842 16           0.0       0.0       0.0   
26     5         A    1,820 1,830 12           0.0       0.0       0.0   
26     4         S    1,811 1,820 1,949        0.0       0.0       0.0   
26     3         S    1,795 1,811 2,114        0.0       0.0       0.0   
26     2         S    1,777 1,795 2,136        0.0       0.0       0.0   
26     11        A    1,772 1,777 844          0.0       0.0       0.0   
26     10        A    1,763 1,772 16           0.0       0.0       0.0   
24     9         A    1,656 1,664 80           0.0       0.0       0.0   
23     8         A    1,646 1,656 8            0.0       0.0       0.0   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       63    
C    0.04941   9     
S    0.0       27    
==== ========= ======

Duplicated sources
------------------
['1', '10', '2', '3', '4', '5', '6', '7', '8', '9']
Found 11 source(s) with the same ID and 10 true duplicate(s)
Here is a fake duplicate: 11

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.23546 0.01959 0.20655 0.25809 9      
preclassical       0.00526 0.00398 0.00132 0.01887 40     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================= =========
task               sent                                                          received 
read_source_models converter=2.75 KB fnames=963 B                                143.15 KB
preclassical       srcs=163.3 KB params=21.8 KB srcfilter=12.62 KB gsims=5.74 KB 11.85 KB 
================== ============================================================= =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 2.11911  0.37109   9     
total preclassical       0.21044  0.0       40    
managing sources         0.02629  0.0       1     
aggregate curves         0.00460  0.0       40    
store source_info        0.00155  0.0       1     
======================== ======== ========= ======