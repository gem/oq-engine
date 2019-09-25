Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     2,852,175,627      
date           2019-09-24T15:21:16
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 27

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
====================== ======= =============== ================
smlt_path              weight  gsim_logic_tree num_realizations
====================== ======= =============== ================
b1_mfd1_high_dip_dip30 0.01320 trivial(1)      1               
b1_mfd1_high_dip_dip45 0.03960 trivial(1)      1               
b1_mfd1_high_dip_dip60 0.01320 trivial(1)      1               
b1_mfd1_low_dip_dip30  0.01320 trivial(1)      1               
b1_mfd1_low_dip_dip45  0.03960 trivial(1)      1               
b1_mfd1_low_dip_dip60  0.01320 trivial(1)      1               
b1_mfd1_mid_dip_dip30  0.03960 trivial(1)      1               
b1_mfd1_mid_dip_dip45  0.11880 trivial(1)      1               
b1_mfd1_mid_dip_dip60  0.03960 trivial(1)      1               
b1_mfd2_high_dip_dip30 0.01360 trivial(1)      1               
b1_mfd2_high_dip_dip45 0.04080 trivial(1)      1               
b1_mfd2_high_dip_dip60 0.01360 trivial(1)      1               
b1_mfd2_low_dip_dip30  0.01360 trivial(1)      1               
b1_mfd2_low_dip_dip45  0.04080 trivial(1)      1               
b1_mfd2_low_dip_dip60  0.01360 trivial(1)      1               
b1_mfd2_mid_dip_dip30  0.04080 trivial(1)      1               
b1_mfd2_mid_dip_dip45  0.12240 trivial(1)      1               
b1_mfd2_mid_dip_dip60  0.04080 trivial(1)      1               
b1_mfd3_high_dip_dip30 0.01320 trivial(1)      1               
b1_mfd3_high_dip_dip45 0.03960 trivial(1)      1               
b1_mfd3_high_dip_dip60 0.01320 trivial(1)      1               
b1_mfd3_low_dip_dip30  0.01320 trivial(1)      1               
b1_mfd3_low_dip_dip45  0.03960 trivial(1)      1               
b1_mfd3_low_dip_dip60  0.01320 trivial(1)      1               
b1_mfd3_mid_dip_dip30  0.03960 trivial(1)      1               
b1_mfd3_mid_dip_dip45  0.11880 trivial(1)      1               
b1_mfd3_mid_dip_dip60  0.03960 trivial(1)      1               
====================== ======= =============== ================

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

  <RlzsAssoc(size=27, rlzs=27)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 444          296         
source_model.xml 1      Active Shallow Crust 208          296         
source_model.xml 2      Active Shallow Crust 149          296         
source_model.xml 3      Active Shallow Crust 534          296         
source_model.xml 4      Active Shallow Crust 298          296         
source_model.xml 5      Active Shallow Crust 239          296         
source_model.xml 6      Active Shallow Crust 474          296         
source_model.xml 7      Active Shallow Crust 238          296         
source_model.xml 8      Active Shallow Crust 179          296         
source_model.xml 9      Active Shallow Crust 436          296         
source_model.xml 10     Active Shallow Crust 200          296         
source_model.xml 11     Active Shallow Crust 141          296         
source_model.xml 12     Active Shallow Crust 465          296         
source_model.xml 13     Active Shallow Crust 229          296         
source_model.xml 14     Active Shallow Crust 170          296         
source_model.xml 15     Active Shallow Crust 436          296         
source_model.xml 16     Active Shallow Crust 200          296         
source_model.xml 17     Active Shallow Crust 141          296         
source_model.xml 18     Active Shallow Crust 483          296         
source_model.xml 19     Active Shallow Crust 247          296         
source_model.xml 20     Active Shallow Crust 188          296         
source_model.xml 21     Active Shallow Crust 582          296         
source_model.xml 22     Active Shallow Crust 346          296         
source_model.xml 23     Active Shallow Crust 287          296         
source_model.xml 24     Active Shallow Crust 516          296         
source_model.xml 25     Active Shallow Crust 280          296         
source_model.xml 26     Active Shallow Crust 221          296         
================ ====== ==================== ============ ============

============= =====
#TRT models   27   
#eff_ruptures 8,331
#tot_ruptures 7,992
============= =====

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
SFLT1     0      S    60           0.02536   9.00000   862          33,988
SFLT2     0      S    384          0.00716   3.00000   621          86,761
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.03252   54    
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 12 duplicate sources with multiplicity 4.5: ['SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1'
 'SFLT2' 'SFLT2' 'SFLT2']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00345 0.00107 0.00176 0.00568 11     
read_source_models 0.02318 0.00528 0.01935 0.04365 27     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================== ========
task               sent                                           received
preclassical       srcs=12.51 KB srcfilter=6.95 KB params=5.64 KB 3.85 KB 
read_source_models converter=8.28 KB fnames=2.82 KB               50.04 KB
================== ============================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1823                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.62585   0.11328   27    
total preclassical       0.03795   0.0       11    
aggregate curves         0.00316   0.0       11    
store source_info        0.00269   0.0       1     
managing sources         5.555E-04 0.0       1     
======================== ========= ========= ======