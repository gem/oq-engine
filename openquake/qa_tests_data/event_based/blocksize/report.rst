QA test for blocksize independence (hazard)
===========================================

============== ===================
checksum32     2,348,158,649      
date           2018-06-26T14:58:32
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 2, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.5               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1024              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
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
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 2,625        5,572       
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  6            1.69730   0.0        2.00000   292       15    
2         PointSource  6            0.51341   0.0        2.00000   97        13    
3         PointSource  5            0.21586   0.0        2.00000   57        0     
9         PointSource  3            0.00282   0.0        1.50000   2         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  2.42940   4     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00977 0.00340 0.00407 0.01975 59       
compute_hazard     0.09544 0.02554 0.01619 0.15088 28       
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== ================================================================================================== ========
task           sent                                                                                               received
RtreeFilter    srcs=392.08 KB monitor=18.55 KB srcfilter=16.08 KB                                                 149 KB  
compute_hazard sources_or_ruptures=169.4 KB param=63.55 KB monitor=8.8 KB rlzs_by_gsim=8.12 KB src_filter=6.73 KB 36.16 KB
============== ================================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_hazard           2.67234   7.74219   28    
building ruptures              2.59350   6.83203   28    
total prefilter                0.57645   1.19141   59    
splitting sources              0.50570   0.0       1     
reading composite source model 0.50554   0.0       1     
managing sources               0.33993   0.0       1     
saving ruptures                0.03347   0.0       28    
unpickling prefilter           0.02491   0.0       59    
GmfGetter.init                 0.00889   0.20703   28    
unpickling compute_hazard      0.00755   0.0       28    
making contexts                0.00704   0.0       5     
aggregating hcurves            0.00586   0.0       28    
store source_info              0.00477   0.0       1     
reading site collection        2.429E-04 0.0       1     
============================== ========= ========= ======