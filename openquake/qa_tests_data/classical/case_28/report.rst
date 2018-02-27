North Africa PSHA
=================

============== ===================
checksum32     576,018,697        
date           2018-02-25T06:43:08
engine_version 2.10.0-git1f7c0c0  
============== ===================

num_sites = 2, num_levels = 133

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     19                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
sites                   `sites.csv <sites.csv>`_                                    
source                  `GridSources.xml <GridSources.xml>`_                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============================= ====== =============== ================
smlt_path                     weight gsim_logic_tree num_realizations
============================= ====== =============== ================
smoothed_model_m_m0.2_b_e0.0  0.500  simple(0,4,0)   4/4             
smoothed_model_m_m0.2_b_m0.05 0.500  simple(0,4,0)   4/4             
============================= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================================================================== =========== ======================= =================
grp_id gsims                                                                                  distances   siteparams              ruptparams       
====== ====================================================================================== =========== ======================= =================
0      AkkarEtAlRjb2014() AtkinsonBoore2006Modified2011() ChiouYoungs2014() PezeshkEtAl2011() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      AkkarEtAlRjb2014() AtkinsonBoore2006Modified2011() ChiouYoungs2014() PezeshkEtAl2011() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ====================================================================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,AkkarEtAlRjb2014(): [1]
  0,AtkinsonBoore2006Modified2011(): [2]
  0,ChiouYoungs2014(): [0]
  0,PezeshkEtAl2011(): [3]
  1,AkkarEtAlRjb2014(): [5]
  1,AtkinsonBoore2006Modified2011(): [6]
  1,ChiouYoungs2014(): [4]
  1,PezeshkEtAl2011(): [7]>

Number of ruptures per tectonic region type
-------------------------------------------
=============== ====== =============== ============ ============
source_model    grp_id trt             eff_ruptures tot_ruptures
=============== ====== =============== ============ ============
GridSources.xml 0      Tectonic_type_b 260          260         
GridSources.xml 1      Tectonic_type_b 260          260         
=============== ====== =============== ============ ============

============= ===
#TRT models   2  
#eff_ruptures 520
#tot_ruptures 520
#tot_weight   208
============= ===

Informational data
------------------
======================= ============================================================================
count_ruptures.received tot 1.62 KB, max_per_task 827 B                                             
count_ruptures.sent     param 3.7 KB, sources 3.26 KB, srcfilter 1.52 KB, gsims 794 B, monitor 660 B
hazard.input_weight     52.0                                                                        
hazard.n_imts           7                                                                           
hazard.n_levels         133                                                                         
hazard.n_realizations   32                                                                          
hazard.n_sites          2                                                                           
hazard.n_sources        2                                                                           
hazard.output_weight    266.0                                                                       
hostname                tstation.gem.lan                                                            
require_epsilons        False                                                                       
======================= ============================================================================

Slowest sources
---------------
========= ================ ============ ========= ========= =========
source_id source_class     num_ruptures calc_time num_sites num_split
========= ================ ============ ========= ========= =========
21        MultiPointSource 260          9.754E-04 5         4        
========= ================ ============ ========= ========= =========

Computation times by source typology
------------------------------------
================ ========= ======
source_class     calc_time counts
================ ========= ======
MultiPointSource 9.754E-04 1     
================ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_ruptures     0.004 3.618E-04 0.004 0.004 2        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.008     0.234     2     
store source_info              0.004     0.0       1     
managing sources               0.004     0.0       1     
reading composite source model 0.003     0.0       1     
reading site collection        1.457E-04 0.0       1     
saving probability maps        3.552E-05 0.0       1     
aggregate curves               3.195E-05 0.0       2     
============================== ========= ========= ======