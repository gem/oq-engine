Classical PSHA with NZ NSHM
===========================

============== ===================
checksum32     865,392,691        
date           2018-03-26T15:56:15
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 1, num_levels = 29

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ======================================================================
Name                    File                                                                  
======================= ======================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                          
job_ini                 `job.ini <job.ini>`_                                                  
source                  `NSHM_source_model-editedbkgd.xml <NSHM_source_model-editedbkgd.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_          
======================= ======================================================================

Composite source model
----------------------
========= ====== ================ ================
smlt_path weight gsim_logic_tree  num_realizations
========= ====== ================ ================
b1        1.000  trivial(0,1,0,1) 1/1             
========= ====== ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ===================
grp_id gsims               distances siteparams ruptparams         
====== =================== ========= ========== ===================
0      McVerry2006Asc()    rrup      vs30       hypo_depth mag rake
1      McVerry2006SInter() rrup      vs30       hypo_depth mag rake
====== =================== ========= ========== ===================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,McVerry2006Asc(): [0]
  1,McVerry2006SInter(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================================ ====== ==================== ============ ============
source_model                     grp_id trt                  eff_ruptures tot_ruptures
================================ ====== ==================== ============ ============
NSHM_source_model-editedbkgd.xml 0      Active Shallow Crust 40           40          
NSHM_source_model-editedbkgd.xml 1      Subduction Interface 1.000        2           
================================ ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 41   
#tot_ruptures 42   
#tot_weight   6.000
============= =====

Slowest sources
---------------
========= ========================= ============ ========= ========== ========= =========
source_id source_class              num_ruptures calc_time split_time num_sites num_split
========= ========================= ============ ========= ========== ========= =========
21444     CharacteristicFaultSource 1            0.003     2.146E-06  1         1        
1         PointSource               20           4.716E-04 4.768E-06  1         1        
2         PointSource               20           1.078E-04 1.907E-06  1         1        
21445     CharacteristicFaultSource 1            0.0       1.431E-06  0         0        
========= ========================= ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.003     2     
PointSource               5.794E-04 2     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.004 0.003  0.002 0.006 2        
================== ===== ====== ===== ===== =========

Informational data
------------------
============== =========================================================================== ========
task           sent                                                                        received
count_ruptures sources=809.11 KB srcfilter=1.41 KB param=1.23 KB monitor=660 B gsims=245 B 799 B   
============== =========================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.300     0.0       1     
total count_ruptures           0.008     3.344     2     
managing sources               0.008     0.0       1     
store source_info              0.008     0.0       1     
splitting sources              3.724E-04 0.0       1     
reading site collection        3.197E-04 0.0       1     
unpickling count_ruptures      1.628E-04 0.0       2     
aggregate curves               8.869E-05 0.0       2     
saving probability maps        5.102E-05 0.0       1     
============================== ========= ========= ======