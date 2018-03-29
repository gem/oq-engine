Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

============== ===================
checksum32     2,061,302,359      
date           2018-03-26T15:55:50
engine_version 2.10.0-git543cfb0  
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
========================= ====== =============== ================
smlt_path                 weight gsim_logic_tree num_realizations
========================= ====== =============== ================
Alaska_asc_grid_NSHMP2007 1.000  simple(4)       4/4             
========================= ====== =============== ================

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
======================================================================== ====== ==================== ============ ============
source_model                                                             grp_id trt                  eff_ruptures tot_ruptures
======================================================================== ====== ==================== ============ ============
Alaska_asc_grid_NSHMP2007.xml
                    extra_source_model.xml 1      Active Shallow Crust 276          1,104       
======================================================================== ====== ==================== ============ ============

Slowest sources
---------------
========= ================ ============ ========= ========== ========= =========
source_id source_class     num_ruptures calc_time split_time num_sites num_split
========= ================ ============ ========= ========== ========= =========
2         MultiPointSource 1,104        0.001     8.996E-04  4         3        
1         MultiPointSource 160          0.0       3.328E-04  0         0        
========= ================ ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
================ ========= ======
source_class     calc_time counts
================ ========= ======
MultiPointSource 0.001     2     
================ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.003 NaN    0.003 0.003 1        
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ========================================================================= ========
task           sent                                                                      received
count_ruptures sources=2.85 KB srcfilter=1.76 KB param=1.63 KB gsims=418 B monitor=330 B 365 B   
============== ========================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.012     0.0       1     
managing sources               0.008     0.0       1     
store source_info              0.006     0.0       1     
total count_ruptures           0.003     1.336     1     
splitting sources              0.002     0.0       1     
reading site collection        0.001     0.0       1     
unpickling count_ruptures      8.368E-05 0.0       1     
saving probability maps        4.673E-05 0.0       1     
aggregate curves               3.386E-05 0.0       1     
============================== ========= ========= ======