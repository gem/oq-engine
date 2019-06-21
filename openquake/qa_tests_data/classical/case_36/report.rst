applyToSources with multiple sources
====================================

============== ===================
checksum32     3,235,130,248      
date           2019-06-21T09:42:37
engine_version 3.6.0-git17fd0581aa
============== ===================

num_sites = 1, num_levels = 1, num_rlzs = 9

Parameters
----------
=============================== ===================================================================================================================
calculation_mode                'preclassical'                                                                                                     
number_of_logic_tree_samples    9                                                                                                                  
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
=============================================== ======= =============== ================
smlt_path                                       weight  gsim_logic_tree num_realizations
=============================================== ======= =============== ================
b1_b211_b221_b231_b311_b321_b331_b341_b351_b361 0.11111 trivial(0,0,1)  1               
b1_b212_b222_b232_b312_b322_b332_b342_b352_b362 0.11111 trivial(0,0,1)  1               
b1_b213_b223_b233_b313_b323_b333_b343_b353_b363 0.11111 trivial(0,0,1)  1               
=============================================== ======= =============== ================

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
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=9)
  1,'[SadighEtAl1997]': [0 1 2 3 4]
  4,'[SadighEtAl1997]': [5]
  7,'[SadighEtAl1997]': [6 7 8]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 1      Subduction Interface 633          633         
source_model.xml 4      Subduction Interface 656          633         
source_model.xml 7      Subduction Interface 633          633         
================ ====== ==================== ============ ============

============= ======
#TRT models   3     
#eff_ruptures 1,922 
#tot_ruptures 24,093
#tot_weight   24,152
============= ======

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
1      1         C    8     107   633          0.00863   1.00000   633   
4      1         C    215   314   656          0.00830   1.00000   656   
7      1         C    422   521   633          0.00823   1.00000   633   
8      8         A    611   621   8            0.0       0.0       0.0   
8      7         A    600   611   12           0.0       0.0       0.0   
8      6         A    588   600   16           0.0       0.0       0.0   
8      5         A    578   588   12           0.0       0.0       0.0   
8      4         S    569   578   1,949        0.0       0.0       0.0   
8      3         S    553   569   2,114        0.0       0.0       0.0   
8      2         S    535   553   2,136        0.0       0.0       0.0   
8      11        A    530   535   844          0.0       0.0       0.0   
8      10        A    521   530   16           0.0       0.0       0.0   
6      9         A    414   422   80           0.0       0.0       0.0   
5      8         A    404   414   10           0.0       0.0       0.0   
5      7         A    393   404   15           0.0       0.0       0.0   
5      6         A    381   393   20           0.0       0.0       0.0   
5      5         A    371   381   15           0.0       0.0       0.0   
5      4         S    362   371   1,949        0.0       0.0       0.0   
5      3         S    346   362   2,114        0.0       0.0       0.0   
5      2         S    328   346   2,136        0.0       0.0       0.0   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       21    
C    0.02515   3     
S    0.0       9     
==== ========= ======

Duplicated sources
------------------
['2', '3', '4']
Found 11 source(s) with the same ID and 3 true duplicate(s)
Here is a fake duplicate: 1

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00633 0.00366 0.00158 0.01344 18     
read_source_models 0.23880 0.02122 0.22411 0.26313 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== =========================================================== ========
task               sent                                                        received
preclassical       srcs=57.13 KB params=9.81 KB srcfilter=5.7 KB gsims=2.58 KB 5.29 KB 
read_source_models converter=939 B fnames=321 B                                47.72 KB
================== =========================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.71640  0.49609   3     
total preclassical       0.11397  0.0       18    
managing sources         0.01078  0.0       1     
aggregate curves         0.00236  0.0       18    
store source_info        0.00154  0.0       1     
======================== ======== ========= ======