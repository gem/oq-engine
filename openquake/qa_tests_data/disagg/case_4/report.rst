Disaggregation with sampling
============================

============== ===================
checksum32     1_553_247_118      
date           2020-03-13T11:20:22
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 38, num_rlzs = 2

Parameters
----------
=============================== =================
calculation_mode                'preclassical'   
number_of_logic_tree_samples    2                
maximum_distance                {'default': 40.0}
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 2               
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
0      0.06609   2_236        1_619       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
2         0      A    1_440        0.01228   0.06667   1_440       
4         0      C    164          0.00530   0.06098   164         
1         0      P    15           0.00172   0.06667   15          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01228  
C    0.00530  
P    0.00172  
S    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.07070 0.10894 0.00249 0.23332 4      
read_source_model  0.03762 NaN     0.03762 0.03762 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            3.65 KB 
preclassical      srcs=5.8 KB params=3.89 KB srcfilter=892 B 1.4 KB  
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66892                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.28279   2.58203   4     
splitting/filtering sources 0.24268   1.01953   4     
composite source model      0.05033   0.0       1     
total read_source_model     0.03762   0.0       1     
store source_info           0.00244   0.0       1     
aggregate curves            9.310E-04 0.0       3     
=========================== ========= ========= ======