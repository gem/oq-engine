Test when `shift_hypo` option is False
======================================

============== ===================
checksum32     4,277,682,064      
date           2019-10-16T13:25:56
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
1         0      A    200          0.15052   1.00000   200         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.15052  
==== =========

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.01304 NaN     0.01304 0.01304 1      
build_hazard           0.00346 NaN     0.00346 0.00346 1      
classical_split_filter 0.07797 0.04284 0.04768 0.10827 2      
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
calc_951                     time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      1.52452   9.58203   1     
total classical_split_filter 0.15595   1.62500   2     
composite source model       0.14031   5.66016   1     
make_contexts                0.04267   0.0       200   
aggregate curves             0.01602   2.24609   2     
total SourceReader           0.01304   0.33203   1     
get_poes                     0.01199   0.0       200   
computing mean_std           0.00746   0.0       200   
filtering/splitting sources  0.00355   1.37891   1     
total build_hazard           0.00346   0.08984   1     
read PoEs                    0.00296   0.07031   1     
store source_info            0.00200   0.04688   1     
saving probability maps      0.00120   0.01562   1     
saving statistics            7.799E-04 0.00781   1     
compute stats                2.580E-04 0.0       1     
combine pmaps                4.601E-05 0.0       1     
============================ ========= ========= ======