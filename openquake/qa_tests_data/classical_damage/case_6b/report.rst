Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     1,338,208,820      
date           2018-06-05T06:38:24
engine_version 3.2.0-git65c4735   
============== ===================

num_sites = 7, num_levels = 28

Parameters
----------
=============================== ==================
calculation_mode                'classical_damage'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
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
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 482          482         
================ ====== ==================== ============ ============

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
Wood     1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource 482          0.03933   3.200E-04  7.00000   15        0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.03933   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00859 0.00278   0.00221 0.01187 15       
count_eff_ruptures 0.00888 8.511E-04 0.00799 0.01007 6        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=2, weight=246, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   7.00000 0.0    7   7   3
weight   82      66     39  158 3
======== ======= ====== === === =

Slowest task
------------
taskno=4, weight=238, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   7.00000 0.0    7   7   2
weight   119     0.0    119 119 2
======== ======= ====== === === =

Data transfer
-------------
================== ============================================================================ ========
task               sent                                                                         received
RtreeFilter        srcs=15.36 KB monitor=5.07 KB srcfilter=4.09 KB                              17.35 KB
count_eff_ruptures sources=11.03 KB param=3.71 KB monitor=2.07 KB srcfilter=1.37 KB gsims=720 B 2.1 KB  
================== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.44902   0.0       1     
managing sources               0.23759   0.0       1     
total prefilter                0.12883   5.19141   15    
total count_eff_ruptures       0.05331   5.75781   6     
reading composite source model 0.01074   0.0       1     
unpickling prefilter           0.00714   0.0       15    
store source_info              0.00608   0.0       1     
reading site collection        0.00358   0.0       1     
reading exposure               0.00222   0.0       1     
aggregate curves               0.00188   0.0       6     
unpickling count_eff_ruptures  0.00163   0.0       6     
splitting sources              7.818E-04 0.0       1     
saving probability maps        2.136E-04 0.0       1     
============================== ========= ========= ======