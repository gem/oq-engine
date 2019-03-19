applyToSources with multiple sources
====================================

============== ===================
checksum32     1,660,043,577      
date           2019-03-19T10:05:15
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 1, num_levels = 1, num_rlzs = 2

Parameters
----------
=============================== ==================================================================================================
calculation_mode                'preclassical'                                                                                    
number_of_logic_tree_samples    2                                                                                                 
maximum_distance                {'Active Shallow Crust': 30.0, 'Subduction Interface': 100.0, 'Stable Continental Interior': 30.0}
investigation_time              1.0                                                                                               
ses_per_logic_tree_path         1                                                                                                 
truncation_level                None                                                                                              
rupture_mesh_spacing            5.0                                                                                               
complex_fault_mesh_spacing      50.0                                                                                              
width_of_mfd_bin                0.5                                                                                               
area_source_discretization      50.0                                                                                              
ground_motion_correlation_model None                                                                                              
minimum_intensity               {}                                                                                                
random_seed                     42                                                                                                
master_seed                     0                                                                                                 
ses_seed                        42                                                                                                
=============================== ==================================================================================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============ ======= =============== ================
smlt_path    weight  gsim_logic_tree num_realizations
============ ======= =============== ================
b1_b231_b361 0.50000 trivial(0)      0               
============ ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===== ========= ========== ==========
grp_id gsims distances siteparams ruptparams
====== ===== ========= ========== ==========
0            rrup                           
1            rrup                           
2            rrup                           
====== ===== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=2)
  1,'[FromFile]': [0 1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 1      Subduction Interface 596          633         
================ ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
2      8         A    197   207   8            0.0       0.0        0.0       0         0.0   
2      7         A    186   197   12           0.0       0.0        0.0       0         0.0   
2      6         A    174   186   16           0.0       0.0        0.0       0         0.0   
2      5         A    164   174   12           0.0       0.0        0.0       0         0.0   
2      4         S    155   164   1,949        0.0       0.0        0.0       0         0.0   
2      3         S    139   155   2,114        0.0       0.0        0.0       0         0.0   
2      2         S    121   139   2,136        0.0       0.0        0.0       0         0.0   
2      11        A    116   121   1,055        0.0       0.0        0.0       0         0.0   
2      10        A    107   116   16           0.0       0.0        0.0       0         0.0   
1      1         C    8     107   633          0.0       6.37163    7.00000   7         2,384 
0      9         A    0     8     80           0.0       0.0        0.0       0         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       7     
C    0.0       1     
S    0.0       3     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.19164 NaN    0.19164 0.19164 1      
split_filter       0.91332 NaN    0.91332 0.91332 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ========================================= =========
task               sent                                      received 
read_source_models converter=313 B fnames=107 B              15.91 KB 
split_filter       srcs=17.09 KB srcfilter=1014 B dummy=42 B 191.22 KB
================== ========================================= =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.91332  4.33203   1     
total read_source_models 0.19164  2.17188   1     
======================== ======== ========= ======