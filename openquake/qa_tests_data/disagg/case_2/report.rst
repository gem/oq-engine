QA test for disaggregation case_2
=================================

============== ===================
checksum32     2,473,169,806      
date           2019-10-01T06:08:25
engine_version 3.8.0-gite0871b5c35
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
============== ======= =============== ================
smlt_path      weight  gsim_logic_tree num_realizations
============== ======= =============== ================
source_model_1 0.50000 simple(2,1)     2               
source_model_2 0.50000 simple(2,0)     2               
============== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[YoungsEtAl1997SSlab]'                   rrup        vs30                    hypo_depth mag   
1      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=4)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   1,815        1,815       
2      2.00000   3,630        3,630       
2      1.00000   1,420        1,420       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
1         2      S    1,420        0.00615   1.00000   1,420        230,742
2         0      A    1,815        0.00397   1.00000   1,815        457,217
3         1      A    1,815        0.00313   1.00000   1,815        580,720
1         1      A    1,815        0.00294   1.00000   1,815        616,859
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.01004   3     
S    0.00615   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.02736 0.02620 0.00884 0.04589 2      
preclassical       0.00460 0.00139 0.00358 0.00663 4      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.38 KB ltmodel=402 B fname=190 B 9.13 KB 
preclassical srcs=6.9 KB params=1.97 KB gsims=973 B      1.34 KB 
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_23147             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.06237  0.0       1     
total SourceReader     0.05473  0.0       2     
total preclassical     0.01839  0.0       4     
store source_info      0.00203  0.0       1     
aggregate curves       0.00163  0.0       4     
====================== ======== ========= ======