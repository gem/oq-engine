Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2019-09-24T15:20:51
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 12, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical_risk'  
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

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
====== =================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,613        33,831      
================ ====== ==================== ============ ============

Exposure model
--------------
=========== ==
#assets     13
#taxonomies 4 
=========== ==

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
W        1.00000 0.0     1   1   5         5         
A        1.00000 0.0     1   1   4         4         
DS       2.00000 NaN     2   2   1         2         
UFB      1.00000 0.0     1   1   2         2         
*ALL*    1.08333 0.28868 1   2   12        13        
======== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
232       0      A    1,612        1.89879   5,756     1,612        848    
225       0      A    520          0.16069   1.00000   1.00000      6.22329
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.05948   15    
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
build_hazard           0.00696 0.00189 0.00374 0.00948 12     
classical_split_filter 0.53431 0.89976 0.02908 1.88180 4      
read_source_models     0.91436 NaN     0.91436 0.91436 1      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== =============================================== ========
task                   sent                                            received
build_hazard           pgetter=5.77 KB hstats=780 B N=60 B             5.07 KB 
classical_split_filter srcs=28.52 KB srcfilter=15.98 KB params=8.86 KB 4.76 KB 
read_source_models     converter=314 B fnames=111 B                    13.76 KB
====================== =============================================== ========

Slowest operations
------------------
============================ ========= ========= ======
calc_1705                    time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      3.02197   1.09375   1     
total classical_split_filter 2.13725   0.60547   4     
make_contexts                0.95666   0.0       1,846 
total read_source_models     0.91436   0.43359   1     
computing mean_std           0.24846   0.0       1,613 
get_poes                     0.12916   0.0       1,613 
total build_hazard           0.08353   1.65234   12    
read PoEs                    0.07505   1.65234   12    
filtering/splitting sources  0.07413   0.07031   2     
building riskinputs          0.03037   0.0       1     
saving statistics            0.00643   0.0       12    
store source_info            0.00282   1.09375   1     
compute stats                0.00240   0.0       9     
aggregate curves             0.00178   0.0       4     
saving probability maps      0.00165   0.0       1     
combine pmaps                8.056E-04 0.0       12    
reading exposure             4.940E-04 0.0       1     
managing sources             3.605E-04 0.0       1     
============================ ========= ========= ======