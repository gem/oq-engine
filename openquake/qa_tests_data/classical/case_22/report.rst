Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

============== ===================
checksum32     2,061,302,359      
date           2018-05-15T04:13:13
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 21, num_levels = 114

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
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
======================= ================================================================
Name                    File                                                            
======================= ================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                    
job_ini                 `job.ini <job.ini>`_                                            
sites                   `sites.csv <sites.csv>`_                                        
source                  `Alaska_asc_grid_NSHMP2007.xml <Alaska_asc_grid_NSHMP2007.xml>`_
source                  `extra_source_model.xml <extra_source_model.xml>`_              
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_    
======================= ================================================================

Composite source model
----------------------
========================= ======= =============== ================
smlt_path                 weight  gsim_logic_tree num_realizations
========================= ======= =============== ================
Alaska_asc_grid_NSHMP2007 1.00000 simple(4)       4/4             
========================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================================================== ========= ========== ============
grp_id gsims                                                                                                distances siteparams ruptparams  
====== ==================================================================================================== ========= ========== ============
1      AbrahamsonSilva1997() BooreEtAl1997GeometricMean() CampbellBozorgnia2003NSHMP2007() SadighEtAl1997() rjb rrup  vs30       dip mag rake
====== ==================================================================================================== ========= ========== ============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  1,AbrahamsonSilva1997(): [0]
  1,BooreEtAl1997GeometricMean(): [1]
  1,CampbellBozorgnia2003NSHMP2007(): [2]
  1,SadighEtAl1997(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
==================================================== ====== ==================== ============ ============
source_model                                         grp_id trt                  eff_ruptures tot_ruptures
==================================================== ====== ==================== ============ ============
Alaska_asc_grid_NSHMP2007.xml extra_source_model.xml 1      Active Shallow Crust 368          1,104       
==================================================== ====== ==================== ============ ============

Slowest sources
---------------
========= ================ ============ ========= ========== ========= ========= ======
source_id source_class     num_ruptures calc_time split_time num_sites num_split events
========= ================ ============ ========= ========== ========= ========= ======
2         MultiPointSource 1,104        2.513E-04 3.793E-04  5         4         0     
1         MultiPointSource 160          0.0       1.490E-04  0         0         0     
========= ================ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================ ========= ======
source_class     calc_time counts
================ ========= ======
MultiPointSource 2.513E-04 2     
================ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00463 0.00109 0.00242 0.00616 14       
count_ruptures     0.00455 NaN     0.00455 0.00455 1        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=1, weight=162, duration=0 s, sources="2"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   1.25000 0.50000 1   2   4
weight   40      7.62153 36  52  4
======== ======= ======= === === =

Slowest task
------------
taskno=1, weight=162, duration=0 s, sources="2"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   1.25000 0.50000 1   2   4
weight   40      7.62153 36  52  4
======== ======= ======= === === =

Informational data
------------------
============== ========================================================================= ========
task           sent                                                                      received
prefilter      srcs=21.95 KB monitor=4.46 KB srcfilter=3.13 KB                           7.04 KB 
count_ruptures sources=4.04 KB srcfilter=1.76 KB param=1.62 KB gsims=418 B monitor=333 B 359 B   
============== ========================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                0.06478   3.83594   14    
managing sources               0.04500   0.0       1     
reading composite source model 0.00532   0.0       1     
total count_ruptures           0.00455   2.12109   1     
store source_info              0.00368   0.0       1     
splitting sources              9.542E-04 0.0       1     
reading site collection        8.094E-04 0.0       1     
unpickling prefilter           3.989E-04 0.0       14    
unpickling count_ruptures      4.101E-05 0.0       1     
saving probability maps        2.885E-05 0.0       1     
aggregate curves               2.003E-05 0.0       1     
============================== ========= ========= ======