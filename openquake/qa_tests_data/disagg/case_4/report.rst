Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2019-07-30T15:03:56
engine_version 3.7.0-git3b3dff46da
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

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,619        2,236       
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== =========
source_id grp_id code num_ruptures calc_time num_sites weight speed    
========= ====== ==== ============ ========= ========= ====== =========
4         0      C    164          0.00257   1.00000   164    63,934   
1         0      P    15           0.00169   1.00000   15     8,859    
2         0      A    1,440        0.00128   1.00000   1,440  1,124,730
========= ====== ==== ============ ========= ========= ====== =========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00128   1     
C    0.00257   1     
P    0.00169   1     
S    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00274 0.00128 0.00156 0.00448 4      
read_source_models 0.03085 NaN     0.03085 0.03085 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================================= ========
task               sent                                                    received
preclassical       srcs=5.33 KB params=3.43 KB srcfilter=880 B gsims=620 B 1.29 KB 
read_source_models converter=314 B fnames=96 B                             3.74 KB 
================== ======================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15506               time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.03085   0.0       1     
total preclassical       0.01098   0.0       4     
managing sources         0.00539   0.0       1     
store source_info        0.00198   0.0       1     
aggregate curves         5.004E-04 0.0       4     
======================== ========= ========= ======