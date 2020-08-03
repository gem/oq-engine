Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     3_516_643_643      
date           2020-03-13T11:22:10
engine_version 3.9.0-gitfb3ef3a732
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
pointsource_distance            {'default': {}}   
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
====================== ======= ================
smlt_path              weight  num_realizations
====================== ======= ================
b1_mfd1_high_dip_dip30 0.01320 1               
b1_mfd1_high_dip_dip45 0.03960 1               
b1_mfd1_high_dip_dip60 0.01320 1               
b1_mfd1_low_dip_dip30  0.01320 1               
b1_mfd1_low_dip_dip45  0.03960 1               
b1_mfd1_low_dip_dip60  0.01320 1               
b1_mfd1_mid_dip_dip30  0.03960 1               
b1_mfd1_mid_dip_dip45  0.11880 1               
b1_mfd1_mid_dip_dip60  0.03960 1               
b1_mfd2_high_dip_dip30 0.01360 1               
b1_mfd2_high_dip_dip45 0.04080 1               
b1_mfd2_high_dip_dip60 0.01360 1               
b1_mfd2_low_dip_dip30  0.01360 1               
b1_mfd2_low_dip_dip45  0.04080 1               
b1_mfd2_low_dip_dip60  0.01360 1               
b1_mfd2_mid_dip_dip30  0.04080 1               
b1_mfd2_mid_dip_dip45  0.12240 1               
b1_mfd2_mid_dip_dip60  0.04080 1               
b1_mfd3_high_dip_dip30 0.01320 1               
b1_mfd3_high_dip_dip45 0.03960 1               
b1_mfd3_high_dip_dip60 0.01320 1               
b1_mfd3_low_dip_dip30  0.01320 1               
b1_mfd3_low_dip_dip45  0.03960 1               
b1_mfd3_low_dip_dip60  0.01320 1               
b1_mfd3_mid_dip_dip30  0.03960 1               
b1_mfd3_mid_dip_dip45  0.11880 1               
b1_mfd3_mid_dip_dip60  0.03960 1               
====================== ======= ================

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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.00676   444          444         
1      0.01351   148          148         
2      0.02247   89           89          
3      0.00667   150          150         
6      0.01111   90           90          
9      0.04000   25           25          
12     0.01235   81           81          
15     0.03704   27           27          
18     0.01010   99           99          
21     0.00505   198          198         
24     0.00758   132          132         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
SFLT2     0      S    384          0.00989   0.00521   384         
SFLT1     9      S    25           0.00622   0.04000   25          
SFLT1     24     S    132          0.00610   0.00758   132         
SFLT1     18     S    99           0.00608   0.01010   99          
SFLT1     15     S    27           0.00606   0.03704   27          
SFLT2     2      S    89           0.00528   0.02247   89          
SFLT2     1      S    148          0.00442   0.01351   148         
SFLT1     21     S    198          0.00312   0.00505   198         
SFLT1     6      S    90           0.00308   0.01111   90          
SFLT1     3      S    150          0.00302   0.00667   150         
SFLT1     0      S    60           0.00302   0.01667   60          
SFLT1     12     S    81           0.00289   0.01235   81          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.05917  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00601 0.00241 0.00354 0.01147 12     
read_source_model  0.01856 NaN     0.01856 0.01856 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ============================================== ========
task              sent                                           received
read_source_model                                                1.81 KB 
preclassical      srcs=15.02 KB params=7.57 KB srcfilter=2.61 KB 4.5 KB  
================= ============================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66985                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.52844  0.0       1     
total preclassical          0.07210  1.32422   12    
total read_source_model     0.01856  0.0       1     
splitting/filtering sources 0.00424  0.0       12    
aggregate curves            0.00264  0.0       12    
store source_info           0.00260  0.0       1     
=========================== ======== ========= ======