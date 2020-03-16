QA test for disaggregation case_2
=================================

============== ===================
checksum32     869_570_826        
date           2020-03-13T11:20:32
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 1, num_rlzs = 4

Parameters
----------
=============================== =================
calculation_mode                'preclassical'   
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              1.0              
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            4.0              
complex_fault_mesh_spacing      4.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
pointsource_distance            {'default': {}}  
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

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
============== ======= ================
smlt_path      weight  num_realizations
============== ======= ================
source_model_1 0.50000 2               
source_model_2 0.50000 2               
============== ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[YoungsEtAl1997SSlab]'                   rrup        vs30                    hypo_depth mag   
3      '[YoungsEtAl1997SSlab]'                   rrup        vs30                    hypo_depth mag   
====== ========================================= =========== ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.06667   3_630        3_630       
1      0.01056   1_420        1_420       
2      0.06667   1_815        1_815       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         1      S    1_420        0.02446   0.01056   1_420       
1         0      A    1_815        0.01483   0.06667   1_815       
3         0      A    1_815        0.01478   0.06667   1_815       
2         2      A    1_815        0.01473   0.06667   1_815       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.04434  
S    0.02446  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.03100 0.00396 0.02556 0.03505 4      
read_source_model  0.02571 0.02397 0.00876 0.04266 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model converter=664 B fname=190 B srcfilter=8 B 5.25 KB 
preclassical      srcs=7.26 KB params=2.44 KB gsims=973 B   1.45 KB 
================= ========================================= ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66896                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.44623  0.0       1     
total preclassical          0.12398  1.64844   4     
total read_source_model     0.05142  0.43359   2     
splitting/filtering sources 0.04909  0.30078   4     
store source_info           0.00211  0.0       1     
aggregate curves            0.00114  0.0       4     
=========================== ======== ========= ======