Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2019-10-02T10:07:04
engine_version 3.8.0-git6f03622c6e
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      5,757     33,831       1,613       
====== ========= ============ ============

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
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
232       0      A    1,612        1.94711   3.57072   1,612       
225       0      A    520          0.16194   1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.10905   15    
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.99284 NaN     0.99284 0.99284 1      
build_hazard           0.00619 0.00160 0.00335 0.00820 12     
classical_split_filter 0.54803 0.92243 0.03267 1.92964 4      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ============================================== ========
task                   sent                                           received
SourceReader                                                          26.26 KB
build_hazard           pgetter=5.78 KB hstats=780 B N=60 B            5.07 KB 
classical_split_filter srcs=28.28 KB params=8.86 KB srcfilter=3.05 KB 4.76 KB 
====================== ============================================== ========

Slowest operations
------------------
============================ ========= ========= ======
calc_29400                   time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      3.14894   0.44531   1     
total classical_split_filter 2.19212   1.04688   4     
composite source model       1.00551   0.0       1     
total SourceReader           0.99284   0.0       1     
make_contexts                0.98954   0.0       1,846 
computing mean_std           0.24241   0.0       1,613 
get_poes                     0.13441   0.0       1,613 
filtering/splitting sources  0.07940   0.83984   2     
total build_hazard           0.07424   1.21875   12    
read PoEs                    0.06667   1.21875   12    
building riskinputs          0.02967   0.0       1     
saving statistics            0.00583   0.0       12    
store source_info            0.00246   0.0       1     
saving probability maps      0.00181   0.0       1     
aggregate curves             0.00179   0.0       4     
compute stats                0.00147   0.0       9     
combine pmaps                8.013E-04 0.0       12    
reading exposure             6.068E-04 0.0       1     
============================ ========= ========= ======