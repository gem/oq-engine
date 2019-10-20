Test the use of the `shift_hypo` option
=======================================

============== ===================
checksum32     865,288,112        
date           2019-10-16T13:09:46
engine_version 3.8.0-git3fc7292edb
============== ===================

num_sites = 1, num_levels = 20, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
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
====== ================ ========== ========== ==========
grp_id gsims            distances  siteparams ruptparams
====== ================ ========== ========== ==========
0      '[Atkinson2015]' rhypo rrup            mag       
====== ================ ========== ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   200          200         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    200          0.15460   1.00000   200         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.15460  
==== =========

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.00885 NaN     0.00885 0.00885 1      
build_hazard           0.00378 NaN     0.00378 0.00378 1      
classical_split_filter 0.08018 0.04431 0.04885 0.11151 2      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ========================================= ========
task                   sent                                      received
classical_split_filter srcs=1.99 KB params=688 B srcfilter=222 B 12.77 KB
====================== ========================================= ========

Slowest operations
------------------
============================ ========= ========= ======
calc_948                     time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      1.48471   9.31641   1     
total classical_split_filter 0.16035   2.14062   2     
composite source model       0.15672   3.77734   1     
make_contexts                0.04382   0.0       200   
aggregate curves             0.01395   0.13281   2     
get_poes                     0.01238   0.0       200   
total SourceReader           0.00885   0.33984   1     
computing mean_std           0.00746   0.0       200   
total build_hazard           0.00378   1.11719   1     
filtering/splitting sources  0.00377   1.87500   1     
read PoEs                    0.00327   1.08984   1     
store source_info            0.00218   0.08203   1     
saving probability maps      0.00153   0.02734   1     
saving statistics            0.00100   0.00781   1     
compute stats                2.613E-04 0.0       1     
combine pmaps                4.625E-05 0.0       1     
============================ ========= ========= ======