QA test for disaggregation case_2
=================================

============== ===================
checksum32     869_570_826        
date           2020-01-16T05:30:50
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None             
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
0      0.06667   1_815        1_815       
1      0.06667   3_630        3_630       
2      0.01056   1_420        1_420       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         2      S    1_420        0.02659   0.01056   1_420       
1         1      A    1_815        0.01675   0.06667   1_815       
2         0      A    1_815        0.01661   0.06667   1_815       
3         1      A    1_815        0.01633   0.06667   1_815       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.04969  
S    0.02659  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.03530 0.02462 0.01789 0.05271 2      
preclassical       0.03864 0.00744 0.02771 0.04402 4      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.44 KB ltmodel=402 B fname=204 B 7.26 KB 
preclassical srcs=6.96 KB params=2.54 KB gsims=973 B     1.43 KB 
============ =========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43229                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          0.15458  0.0       4     
composite source model      0.07331  0.0       1     
splitting/filtering sources 0.07161  0.0       4     
total SourceReader          0.07061  0.0       2     
store source_info           0.00246  0.0       1     
aggregate curves            0.00105  0.0       4     
=========================== ======== ========= ======