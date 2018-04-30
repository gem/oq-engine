Classical PSHA with NZ NSHM
===========================

============== ===================
checksum32     865,392,691        
date           2018-04-30T11:22:16
engine_version 3.1.0-gitb0812f0   
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
========= ======= ================ ================
smlt_path weight  gsim_logic_tree  num_realizations
========= ======= ================ ================
b1        1.00000 trivial(1,0,1,0) 1/1             
========= ======= ================ ================

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
NSHM_source_model-editedbkgd.xml 1      Subduction Interface 2.00000      2           
================================ ====== ==================== ============ ============

============= =======
#TRT models   2      
#eff_ruptures 42     
#tot_ruptures 42     
#tot_weight   6.00000
============= =======

Slowest sources
---------------
========= ========================= ============ ========= ========== ========= ========= ======
source_id source_class              num_ruptures calc_time split_time num_sites num_split events
========= ========================= ============ ========= ========== ========= ========= ======
21444     CharacteristicFaultSource 1            7.844E-05 1.907E-06  1         1         0     
1         PointSource               20           4.125E-05 8.821E-06  1         1         0     
21445     CharacteristicFaultSource 1            1.931E-05 1.431E-06  1         1         0     
2         PointSource               20           1.073E-05 1.669E-06  1         1         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 9.775E-05 2     
PointSource               5.198E-05 2     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
count_ruptures     0.00301 0.00181 0.00173 0.00430 2        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=1, weight=4, duration=0 s, sources="1 2"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 0.0    1       1       2
weight   2.00000 0.0    2.00000 2.00000 2
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=2, weight=2, duration=0 s, sources="21444 21445"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 0.0    1       1       2
weight   1.00000 0.0    1.00000 1.00000 2
======== ======= ====== ======= ======= =

Informational data
------------------
============== ========================================================================== ========
task           sent                                                                       received
count_ruptures sources=809.39 KB srcfilter=1.4 KB param=1.21 KB monitor=660 B gsims=245 B 858 B   
============== ========================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.25579   0.0       1     
total count_ruptures           0.00603   1.32031   2     
managing sources               0.00512   0.0       1     
store source_info              0.00457   0.0       1     
splitting sources              4.897E-04 0.0       1     
reading site collection        3.188E-04 0.0       1     
unpickling count_ruptures      9.298E-05 0.0       2     
aggregate curves               5.388E-05 0.0       2     
saving probability maps        3.362E-05 0.0       1     
============================== ========= ========= ======