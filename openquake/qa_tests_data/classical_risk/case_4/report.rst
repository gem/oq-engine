Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     2,439,591,035      
date           2017-11-08T18:06:21
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 6, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job_haz.ini <job_haz.ini>`_                                
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  simple(2)       2/2             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================================== =========== ======================= =================
grp_id gsims                               distances   siteparams              ruptparams       
====== =================================== =========== ======================= =================
0      AkkarBommer2010() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): [0]
  0,ChiouYoungs2008(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 2           4,195        6,405       
================ ====== ==================== =========== ============ ============

Informational data
------------------
=========================== ==================================================================================
count_eff_ruptures.received tot 15.84 KB, max_per_task 1.58 KB                                                
count_eff_ruptures.sent     sources 76.71 KB, srcfilter 9.66 KB, param 8.46 KB, monitor 3.84 KB, gsims 2.05 KB
hazard.input_weight         2733.0                                                                            
hazard.n_imts               1                                                                                 
hazard.n_levels             19                                                                                
hazard.n_realizations       2                                                                                 
hazard.n_sites              6                                                                                 
hazard.n_sources            2                                                                                 
hazard.output_weight        114.0                                                                             
hostname                    tstation.gem.lan                                                                  
require_epsilons            True                                                                              
=========================== ==================================================================================

Exposure model
--------------
=============== ========
#assets         6       
#taxonomies     2       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 NaN    1   1   1         1         
W        1.000 0.0    1   1   5         5         
*ALL*    1.000 0.0    1   1   6         6         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      231       AreaSource   4,185        0.032     6         279      
0      376       AreaSource   2,220        1.080E-04 1         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.032     2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.004 3.591E-04 0.004 0.005 12       
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 2.035     0.0       1     
managing sources               0.155     0.0       1     
total count_eff_ruptures       0.053     1.965     12    
prefiltering source model      0.020     0.0       1     
reading exposure               0.007     0.0       1     
store source_info              0.003     0.0       1     
aggregate curves               3.974E-04 0.0       12    
saving probability maps        2.432E-05 0.0       1     
reading site collection        6.199E-06 0.0       1     
============================== ========= ========= ======