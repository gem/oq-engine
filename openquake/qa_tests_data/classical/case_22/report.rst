Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

============== ===================
checksum32     4,227,047,805      
date           2017-12-06T11:20:01
engine_version 2.9.0-gite55e76e   
============== ===================

num_sites = 21, num_imts = 6

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
random_seed                     23                
master_seed                     0                 
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

Informational data
------------------
======================= =============================================================================
count_ruptures.received max_per_task 662 B, tot 662 B                                                
count_ruptures.sent     sources 2.85 KB, param 1.63 KB, srcfilter 1.21 KB, gsims 353 B, monitor 319 B
hazard.input_weight     126.4                                                                        
hazard.n_imts           6                                                                            
hazard.n_levels         114                                                                          
hazard.n_realizations   4                                                                            
hazard.n_sites          21                                                                           
hazard.n_sources        2                                                                            
hazard.output_weight    2394.0                                                                       
hostname                tstation.gem.lan                                                             
require_epsilons        False                                                                        
======================= =============================================================================

Slowest sources
---------------
========= ================ ============ ========= ========= =========
source_id source_class     num_ruptures calc_time num_sites num_split
========= ================ ============ ========= ========= =========
mps-0     MultiPointSource 1,104        5.548E-04 2         3        
========= ================ ============ ========= ========= =========

Computation times by source typology
------------------------------------
================ ========= ======
source_class     calc_time counts
================ ========= ======
MultiPointSource 5.548E-04 1     
================ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.002 NaN    0.002 0.002 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.006     0.0       1     
reading composite source model 0.004     0.0       1     
store source_info              0.004     0.0       1     
total count_ruptures           0.002     0.0       1     
reading site collection        2.608E-04 0.0       1     
saving probability maps        2.980E-05 0.0       1     
aggregate curves               1.955E-05 0.0       1     
============================== ========= ========= ======