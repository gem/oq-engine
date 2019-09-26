Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2019-09-24T15:20:59
engine_version 3.7.0-git749bb363b3
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
========= ====== ==== ============ ========= ========= ============ =========
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed    
========= ====== ==== ============ ========= ========= ============ =========
4         0      C    164          0.00161   1.00000   164          101,831  
1         0      P    15           3.424E-04 1.00000   15           43,812   
2         0      A    1,440        2.615E-04 1.00000   1,440        5,505,741
========= ====== ==== ============ ========= ========= ============ =========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.615E-04 1     
C    0.00161   1     
P    3.424E-04 1     
S    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =======
operation-duration mean    stddev  min       max     outputs
preclassical       0.00192 0.00163 7.491E-04 0.00422 4      
read_source_models 0.04901 NaN     0.04901   0.04901 1      
================== ======= ======= ========= ======= =======

Data transfer
-------------
================== ============================================ ========
task               sent                                         received
preclassical       srcs=5.35 KB params=3.43 KB srcfilter=2.8 KB 1.29 KB 
read_source_models converter=314 B fnames=103 B                 3.74 KB 
================== ============================================ ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1738                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.04901   0.49609   1     
total preclassical       0.00767   0.0       4     
store source_info        0.00269   0.0       1     
aggregate curves         0.00156   0.0       4     
managing sources         4.125E-04 0.0       1     
======================== ========= ========= ======