Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2019-10-01T06:32:21
engine_version 3.8.0-git66affb82eb
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
0      3.00000   2,236        1,619       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
4         0      C    164          0.00445   1.00000   164          36,814 
1         0      P    15           0.00237   1.00000   15           6,321  
2         0      A    1,440        0.00227   1.00000   1,440        633,169
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00227   1     
C    0.00445   1     
P    0.00237   1     
S    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.03411 NaN     0.03411 0.03411 1      
preclassical       0.00419 0.00164 0.00280 0.00615 4      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader                                             6.61 KB 
preclassical srcs=5.29 KB params=3.43 KB srcfilter=888 B 1.29 KB 
============ =========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_6391              time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.04192   0.0       1     
total SourceReader     0.03411   0.0       1     
total preclassical     0.01676   0.25781   4     
store source_info      0.00198   0.0       1     
aggregate curves       9.637E-04 0.0       4     
====================== ========= ========= ======