Classical PSHA with NZ NSHM
===========================

============== ===================
checksum32     865,392,691        
date           2018-09-05T10:04:54
engine_version 3.2.0-gitb4ef3a4b6c
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
21444     CharacteristicFaultSource 1            0.00274   1.431E-06  1.00000   1         0     
1         PointSource               20           0.00141   2.623E-06  1.00000   1         0     
21445     CharacteristicFaultSource 1            2.289E-05 9.537E-07  1.00000   1         0     
2         PointSource               20           1.025E-05 1.192E-06  1.00000   1         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.00276   2     
PointSource               0.00143   2     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.18251 NaN       0.18251 0.18251 1        
count_eff_ruptures   0.00259 0.00118   0.00176 0.00343 2        
preprocess           0.00116 1.713E-04 0.00101 0.00134 4        
==================== ======= ========= ======= ======= =========

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
==================== ======================================================================== ========
task                 sent                                                                     received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                     188 B   
count_eff_ruptures   sources=809.44 KB param=1.4 KB monitor=614 B srcfilter=440 B gsims=245 B 858 B   
preprocess           srcs=810.61 KB monitor=1.25 KB srcfilter=1012 B param=144 B              810.8 KB
==================== ======================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total pickle_source_models 0.18251   0.0       1     
managing sources           0.02036   0.0       1     
total count_eff_ruptures   0.00519   0.0       2     
total preprocess           0.00466   0.0       4     
store source_info          0.00439   0.0       1     
aggregate curves           3.834E-04 0.0       2     
splitting sources          2.420E-04 0.0       1     
========================== ========= ========= ======