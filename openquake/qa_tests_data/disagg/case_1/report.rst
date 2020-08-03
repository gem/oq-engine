QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     2_673_797_252      
date           2020-03-13T11:20:25
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 38, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     9000              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== =========== ======================= =================
grp_id gsims               distances   siteparams              ruptparams       
====== =================== =========== ======================= =================
0      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================== =========== ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.03170   3_691        3_691       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
3         0      S    617          0.01760   0.01621   617         
2         0      A    2_880        0.01189   0.03333   2_880       
4         0      C    164          0.00560   0.06098   164         
1         0      P    30           0.00173   0.03333   30          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01189  
C    0.00560  
P    0.00173  
S    0.01760  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.07215 0.11199 0.00241 0.23938 4      
read_source_model  0.03728 NaN     0.03728 0.03728 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            3.99 KB 
preclassical      srcs=5.8 KB params=3.89 KB srcfilter=892 B 1.44 KB 
================= ========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66894                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          0.28862  2.68750   4     
splitting/filtering sources 0.24847  1.08594   4     
composite source model      0.04979  0.0       1     
total read_source_model     0.03728  0.0       1     
store source_info           0.00244  0.0       1     
aggregate curves            0.00138  0.0       4     
=========================== ======== ========= ======