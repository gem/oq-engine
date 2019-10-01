Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2019-10-01T06:08:25
engine_version 3.8.0-gite0871b5c35
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
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
359       0      A    2,314        2.40570   5,756     1,612        670    
306       0      A    1,768        0.22851   1.00000   1.00000      4.37621
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.63421   15    
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           1.09379 NaN     1.09379 1.09379 1      
build_hazard           0.00578 0.00149 0.00341 0.00766 12     
classical_split_filter 0.70122 1.12086 0.05318 2.37954 4      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ============================================== ========
task                   sent                                           received
SourceReader                                                          24.95 KB
build_hazard           pgetter=5.78 KB hstats=780 B N=60 B            5.07 KB 
classical_split_filter srcs=28.28 KB params=8.86 KB srcfilter=3.05 KB 4.76 KB 
====================== ============================================== ========

Slowest operations
------------------
============================ ========= ========= ======
calc_23149                   time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      3.80959   0.0       1     
total classical_split_filter 2.80487   0.0       4     
make_contexts                1.21620   0.0       1,846 
composite source model       1.10851   0.0       1     
total SourceReader           1.09379   0.0       1     
computing mean_std           0.30627   0.0       1,613 
get_poes                     0.17257   0.0       1,613 
filtering/splitting sources  0.16526   0.0       2     
total build_hazard           0.06941   0.99609   12    
read PoEs                    0.06244   0.99609   12    
building riskinputs          0.03312   0.0       1     
saving statistics            0.00835   0.0       12    
aggregate curves             0.00229   0.0       4     
store source_info            0.00212   0.0       1     
reading exposure             0.00156   0.0       1     
saving probability maps      0.00146   0.0       1     
compute stats                9.451E-04 0.0       9     
combine pmaps                5.834E-04 0.0       12    
============================ ========= ========= ======