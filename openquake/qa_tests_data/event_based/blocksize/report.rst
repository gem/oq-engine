QA test for blocksize independence (hazard)
===========================================

============== ===================
checksum32     3,254,196,570      
date           2018-06-05T06:40:02
engine_version 3.2.0-git65c4735   
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
1         AreaSource   1,752        0.86476   0.10866    2.00000   292       83    
2         AreaSource   582          0.28555   0.03155    2.00000   97        114   
3         AreaSource   440          0.13748   0.02545    2.00000   57        57    
9         AreaSource   222          0.00295   0.02957    1.50000   2         2     
4         AreaSource   267          0.0       0.02765    0.0       0         0     
5         AreaSource   518          0.0       0.09239    0.0       0         0     
6         AreaSource   316          0.0       0.05002    0.0       0         0     
7         AreaSource   1,028        0.0       0.09000    0.0       0         0     
8         AreaSource   447          0.0       0.08560    0.0       0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   1.29074   9     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.01009 0.00616 0.00388 0.03145 59       
compute_ruptures   0.44242 0.10781 0.31794 0.50473 3        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================ ============================================================================ ========
task             sent                                                                         received
RtreeFilter      srcs=392.08 KB monitor=19.94 KB srcfilter=16.08 KB                           149 KB  
compute_ruptures sources=141.54 KB param=1.77 KB monitor=1.03 KB src_filter=699 B gsims=381 B 30.08 KB
================ ============================================================================ ========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
EventBasedRuptureCalculator.run 2.31922   0.0       1     
total compute_ruptures          1.32727   7.14453   3     
managing sources                0.96107   0.0       1     
reading composite source model  0.64309   0.0       1     
total prefilter                 0.59528   3.46875   59    
splitting sources               0.54215   0.0       1     
unpickling prefilter            0.03044   0.0       59    
saving ruptures                 0.00818   0.0       3     
store source_info               0.00485   0.0       1     
making contexts                 0.00411   0.0       5     
unpickling compute_ruptures     0.00245   0.0       3     
setting event years             0.00137   0.0       1     
reading site collection         7.663E-04 0.0       1     
=============================== ========= ========= ======