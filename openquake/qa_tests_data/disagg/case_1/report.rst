QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     3_866_945_601      
date           2020-01-16T05:30:44
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            {'default': 50}   
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== =========== ======================= =================
grp_id gsims               distances   siteparams              ruptparams       
====== =================== =========== ======================= =================
0      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.03333   30           30          
1      0.03333   2_880        2_880       
2      0.01621   617          617         
3      0.06098   164          164         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
3         2      S    617          0.02408   0.01621   617         
2         1      A    2_880        0.01155   0.03333   2_880       
4         3      C    164          0.00489   0.06098   164         
1         0      P    30           0.00265   0.03333   30          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01155  
C    0.00489  
P    0.00265  
S    0.02408  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.04426 NaN     0.04426 0.04426 1      
preclassical       0.08590 0.13093 0.00387 0.28143 4      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ============================================== ========
task         sent                                           received
SourceReader                                                5.58 KB 
preclassical params=39.29 KB srcs=5.33 KB srcfilter=3.92 KB 1.43 KB 
============ ============================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43227                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          0.34361  0.0       4     
splitting/filtering sources 0.29660  0.0       4     
composite source model      0.05747  0.0       1     
total SourceReader          0.04426  0.0       1     
store source_info           0.00240  0.0       1     
aggregate curves            0.00113  0.0       4     
=========================== ======== ========= ======