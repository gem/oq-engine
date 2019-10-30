Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2019-10-23T16:25:46
engine_version 3.8.0-git2e0d8e6795
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
0      3.56913   33,831       1,613       
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
232       0      A    1,612        2.66010   3.57072   1,612       
225       0      A    520          0.16627   1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    2.82636  
==== =========

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           1.53942 NaN     1.53942 1.53942 1      
build_hazard           0.00457 0.00215 0.00268 0.00924 12     
classical_split_filter 1.46068 1.80554 0.18397 2.73739 2      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ============================================== ========
task                   sent                                           received
classical_split_filter srcs=28.28 KB params=9.42 KB srcfilter=3.05 KB 3.08 KB 
build_hazard           pgetter=5.78 KB hstats=780 B N=60 B            5.07 KB 
====================== ============================================== ========

Slowest operations
------------------
============================ ========= ========= ======
calc_44409                   time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      4.47232   0.0       1     
total classical_split_filter 2.92135   0.58203   2     
composite source model       1.55256   0.0       1     
total SourceReader           1.53942   0.0       1     
make_contexts                1.23631   0.0       1,846 
computing mean_std           0.33969   0.0       1,613 
get_poes                     0.21157   0.0       1,613 
filtering/splitting sources  0.09191   0.31641   2     
total build_hazard           0.05489   1.50391   12    
composing pnes               0.05245   0.0       1,613 
read PoEs                    0.05044   1.50391   12    
building riskinputs          0.02600   0.12891   1     
saving statistics            0.02340   0.0       12    
store source_info            0.00219   0.0       1     
saving probability maps      0.00148   0.0       1     
compute stats                8.724E-04 0.0       9     
reading exposure             5.271E-04 0.0       1     
combine pmaps                4.835E-04 0.0       12    
aggregate curves             4.590E-04 0.0       2     
============================ ========= ========= ======