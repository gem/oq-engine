Event Based Risk QA Test 1
==========================

============== ===================
checksum32     908,357,909        
date           2018-09-25T14:28:34
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 3, num_levels = 25

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         20                
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
=========================== ====================================================================
Name                        File                                                                
=========================== ====================================================================
exposure                    `exposure.xml <exposure.xml>`_                                      
gsim_logic_tree             `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                        
job_ini                     `job.ini <job.ini>`_                                                
nonstructural_vulnerability `vulnerability_model_nonstco.xml <vulnerability_model_nonstco.xml>`_
source                      `source_model.xml <source_model.xml>`_                              
source_model_logic_tree     `source_model_logic_tree.xml <source_model_logic_tree.xml>`_        
structural_vulnerability    `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_      
=========================== ====================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2/2             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================================== =========== ======================= =================
grp_id gsims                               distances   siteparams              ruptparams       
====== =================================== =========== ======================= =================
0      AkkarBommer2010() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): [1]
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 18           18          
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 2 realization(s) x 2 loss type(s) x 1 losses x 8 bytes x 60 tasks = 7.5 KB

Exposure model
--------------
=============== ========
#assets         4       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
RM       1.00000 0.0     1   1   2         2         
RC       1.00000 NaN     1   1   1         1         
W        1.00000 NaN     1   1   1         1         
*ALL*    1.33333 0.57735 1   2   3         4         
======== ======= ======= === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         P    0     1     6            0.00979   2.980E-05  1.00000   1         8.00000
0      2         P    1     2     6            0.01057   1.097E-05  1.00000   1         6.00000
0      3         P    2     3     6            0.00688   8.821E-06  1.00000   1         6.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.02724   3     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
read_source_models 0.00137 NaN     0.00137 0.00137 1        
split_filter       0.00356 NaN     0.00356 0.00356 1        
build_ruptures     0.01254 0.00163 0.01086 0.01413 3        
compute_gmfs       0.11148 NaN     0.11148 0.11148 1        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================== ============================================================================================ ========
task               sent                                                                                         received
read_source_models monitor=0 B fnames=0 B converter=0 B                                                         2.2 KB  
split_filter       srcs=2.09 KB monitor=446 B srcfilter=220 B sample_factor=21 B seed=14 B                      2.23 KB 
build_ruptures     srcs=4.15 KB param=1.12 KB monitor=1.12 KB srcfilter=660 B                                   16.53 KB
compute_gmfs       sources_or_ruptures=14.01 KB param=4.05 KB rlzs_by_gsim=418 B monitor=345 B src_filter=220 B 13.62 KB
================== ============================================================================================ ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total compute_gmfs       0.11148   0.0       1     
building hazard          0.10520   0.0       1     
total build_ruptures     0.03762   0.0       3     
making contexts          0.00953   0.0       9     
updating source_info     0.00914   0.0       1     
saving ruptures          0.00854   0.0       3     
store source_info        0.00482   0.0       1     
building riskinputs      0.00478   0.0       1     
managing sources         0.00399   0.0       1     
total split_filter       0.00356   0.0       1     
building ruptures        0.00317   0.0       1     
GmfGetter.init           0.00227   0.0       1     
saving gmf_data/indices  0.00175   0.0       1     
saving gmfs              0.00155   0.0       1     
total read_source_models 0.00153   0.0       3     
setting event years      0.00128   0.0       1     
reading exposure         9.379E-04 0.0       1     
aggregating hcurves      1.435E-04 0.0       1     
======================== ========= ========= ======