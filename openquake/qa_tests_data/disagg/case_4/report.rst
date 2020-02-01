Disaggregation with sampling
============================

============== ===================
checksum32     1_553_247_118      
date           2020-01-16T05:30:44
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None             
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.50000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== =========== ======================= =================
grp_id gsims               distances   siteparams              ruptparams       
====== =================== =========== ======================= =================
0      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=2)>

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
2         0      A    1_440        0.01334   0.06667   1_440       
4         0      C    164          0.00486   0.06098   164         
1         0      P    15           0.00264   0.06667   15          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01334  
C    0.00486  
P    0.00264  
S    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.04356 NaN     0.04356 0.04356 1      
preclassical       0.08252 0.12495 0.00387 0.26874 4      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ======================================== ========
task         sent                                     received
SourceReader                                          5.14 KB 
preclassical srcs=5.34 KB params=4 KB srcfilter=892 B 1.38 KB 
============ ======================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43225                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          0.33009  0.0       4     
splitting/filtering sources 0.28736  0.0       4     
composite source model      0.05551  0.0       1     
total SourceReader          0.04356  0.0       1     
store source_info           0.00246  0.0       1     
aggregate curves            0.00107  0.0       3     
=========================== ======== ========= ======