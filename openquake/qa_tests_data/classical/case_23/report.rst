Classical PSHA with NZ NSHM
===========================

============== ===================
checksum32     865,392,691        
date           2018-06-05T06:39:19
engine_version 3.2.0-git65c4735   
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
NSHM_source_model-editedbkgd.xml 1      Subduction Interface 2            2           
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
1         PointSource               20           0.00554   8.583E-06  1.00000   1         0     
21444     CharacteristicFaultSource 1            0.00534   2.146E-06  1.00000   1         0     
2         PointSource               20           2.003E-05 1.669E-06  1.00000   1         0     
21445     CharacteristicFaultSource 1            1.788E-05 1.669E-06  1.00000   1         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.00536   2     
PointSource               0.00556   2     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00559 0.00264   0.00317 0.00809 4        
count_eff_ruptures 0.00786 5.201E-04 0.00750 0.00823 2        
================== ======= ========= ======= ======= =========

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

Data transfer
-------------
================== ======================================================================== =========
task               sent                                                                     received 
RtreeFilter        srcs=810.76 KB monitor=1.35 KB srcfilter=1.09 KB                         811.08 KB
count_eff_ruptures sources=809.6 KB param=1.25 KB monitor=706 B srcfilter=466 B gsims=245 B 858 B    
================== ======================================================================== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.65928   1.14062   1     
reading composite source model 0.25210   0.0       1     
managing sources               0.19574   0.50391   1     
total prefilter                0.02234   3.66016   4     
total count_eff_ruptures       0.01573   5.65234   2     
store source_info              0.00654   0.0       1     
unpickling prefilter           0.00137   0.0       4     
reading site collection        9.968E-04 0.0       1     
aggregate curves               7.339E-04 0.0       2     
unpickling count_eff_ruptures  5.670E-04 0.0       2     
splitting sources              3.428E-04 0.0       1     
saving probability maps        2.241E-04 0.0       1     
============================== ========= ========= ======