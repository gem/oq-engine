Mutex sources for Nankai, Japan, case_27
========================================

============== ===================
checksum32     3,403,305,238      
date           2019-03-19T10:05:08
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 1, num_levels = 6, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                None              
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================== ========= ========== ==============
grp_id gsims                      distances siteparams ruptparams    
====== ========================== ========= ========== ==============
0      '[SiMidorikawa1999SInter]' rrup      vs30       hypo_depth mag
====== ========================== ========= ========== ==============

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,'[SiMidorikawa1999SInter]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Subduction Interface 19           19          
================ ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1  gidx2  num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= =======
0      case_15   N    44,771 46,988 2            0.0       0.0        1.00000   1         2.00000
0      case_14   N    42,099 44,771 2            0.0       0.0        1.00000   1         2.00000
0      case_13   N    39,684 42,099 2            0.0       0.0        1.00000   1         2.00000
0      case_12   N    36,814 39,684 2            0.0       0.0        1.00000   1         2.00000
0      case_11   N    35,646 36,814 1            0.0       0.0        1.00000   1         1.00000
0      case_10   N    32,222 35,646 1            0.0       0.0        1.00000   1         1.00000
0      case_09   N    30,001 32,222 1            0.0       0.0        1.00000   1         1.00000
0      case_08   N    25,939 30,001 1            0.0       0.0        1.00000   1         1.00000
0      case_07   N    23,263 25,939 1            0.0       0.0        1.00000   1         1.00000
0      case_06   N    19,615 23,263 1            0.0       0.0        1.00000   1         1.00000
0      case_05   N    17,196 19,615 1            0.0       0.0        1.00000   1         1.00000
0      case_04   N    11,470 17,196 1            0.0       0.0        1.00000   1         1.00000
0      case_03   N    7,184  11,470 1            0.0       0.0        1.00000   1         1.00000
0      case_02   N    2,874  7,184  1            0.0       0.0        1.00000   1         1.00000
0      case_01   N    0      2,874  1            0.0       0.0        1.00000   1         1.00000
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.0       15    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.20920 NaN    0.20920 0.20920 1      
only_filter        0.00414 NaN    0.00414 0.00414 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=305 B fnames=107 B            1.08 MB 
only_filter        srcs=1.08 MB srcfilter=253 B dummy=14 B 1.08 MB 
================== ======================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.20920  6.92969   1     
total only_filter        0.00414  1.60156   1     
======================== ======== ========= ======