event based risk
================

============== ===================
checksum32     1,223,742,661      
date           2018-09-25T14:28:24
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 7, num_levels = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              10000.0           
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      None              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
occupants_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 482          482         
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 60 tasks = 3.28 KB

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         S    0     2     482          0.76388   0.01337    105       15        385   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.76388   1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
read_source_models 0.00397 NaN     0.00397 0.00397 1        
split_filter       0.02224 NaN     0.02224 0.02224 1        
build_ruptures     0.05837 0.01872 0.02321 0.09354 14       
compute_gmfs       0.08051 0.02192 0.05617 0.10040 5        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================== ==================================================================================================== =========
task               sent                                                                                                 received 
read_source_models monitor=0 B fnames=0 B converter=0 B                                                                 1.47 KB  
split_filter       srcs=3.12 KB monitor=446 B srcfilter=220 B sample_factor=21 B seed=14 B                              7.01 KB  
build_ruptures     srcs=20.13 KB monitor=5.24 KB param=4.09 KB srcfilter=3.01 KB                                        281.93 KB
compute_gmfs       sources_or_ruptures=273.13 KB param=14.37 KB monitor=1.68 KB rlzs_by_gsim=1.47 KB src_filter=1.07 KB 311.97 KB
================== ==================================================================================================== =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total build_ruptures     0.81721   0.22266   14    
making contexts          0.53008   0.0       259   
total compute_gmfs       0.40254   0.12500   5     
building hazard          0.36103   0.12500   5     
saving ruptures          0.05599   0.0       15    
updating source_info     0.02976   0.0       1     
building riskinputs      0.02325   0.0       1     
total split_filter       0.02224   0.0       1     
building ruptures        0.01735   0.0       5     
GmfGetter.init           0.01672   0.0       5     
managing sources         0.01573   0.0       1     
saving gmfs              0.00807   0.0       5     
store source_info        0.00569   0.0       1     
total read_source_models 0.00419   0.0       3     
saving gmf_data/indices  0.00333   0.0       1     
setting event years      0.00193   0.0       1     
aggregating hcurves      7.596E-04 0.0       5     
reading exposure         6.764E-04 0.0       1     
======================== ========= ========= ======