Classical BCR test
==================

============== ===================
checksum32     233,068,017        
date           2017-10-18T18:22:43
engine_version 2.7.0-git16fce00   
============== ===================

num_sites = 11, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical_bcr'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.5               
area_source_discretization      20.0              
ground_motion_correlation_model None              
random_seed                     42                
master_seed                     0                 
=============================== ==================

Input files
-----------
==================================== ============================================================================
Name                                 File                                                                        
==================================== ============================================================================
exposure                             `exposure_model.xml <exposure_model.xml>`_                                  
gsim_logic_tree                      `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                                
job_ini                              `job.ini <job.ini>`_                                                        
source                               `source_model.xml <source_model.xml>`_                                      
source_model_logic_tree              `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                
structural_vulnerability             `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_  
structural_vulnerability_retrofitted `vulnerability_model_retrofitted.xml <vulnerability_model_retrofitted.xml>`_
==================================== ============================================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ simple(3)       3/3             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================= =========== ======================= =================
grp_id gsims                                                   distances   siteparams              ruptparams       
====== ======================================================= =========== ======================= =================
0      AkkarBommer2010() BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,AkkarBommer2010(): [2]
  0,BooreAtkinson2008(): [1]
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 3           792          828         
================ ====== ==================== =========== ============ ============

Informational data
------------------
=========================== ==================================================================================
count_eff_ruptures.received tot 6.18 KB, max_per_task 1.74 KB                                                 
count_eff_ruptures.sent     sources 27.63 KB, srcfilter 4.71 KB, param 3.14 KB, monitor 1.59 KB, gsims 1.25 KB
hazard.input_weight         831.6000000000001                                                                 
hazard.n_imts               1                                                                                 
hazard.n_levels             8                                                                                 
hazard.n_realizations       3                                                                                 
hazard.n_sites              11                                                                                
hazard.n_sources            3                                                                                 
hazard.output_weight        88.0                                                                              
hostname                    tstation.gem.lan                                                                  
require_epsilons            True                                                                              
=========================== ==================================================================================

Exposure model
--------------
=============== ========
#assets         11      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

========================== ===== ====== === === ========= ==========
taxonomy                   mean  stddev min max num_sites num_assets
Adobe                      1.000 0.0    1   1   2         2         
Stone-Masonry              1.000 0.0    1   1   6         6         
Unreinforced-Brick-Masonry 1.000 NaN    1   1   1         1         
Wood                       1.000 0.0    1   1   2         2         
*ALL*                      1.000 0.0    1   1   11        11        
========================== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      231       AreaSource   414          0.007     11        69       
0      229       AreaSource   264          0.002     8         38       
0      232       AreaSource   150          0.002     11        1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.011     3     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.003 0.001  0.001 0.005 5        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.047     0.0       1     
reading composite source model 0.041     0.0       1     
total count_eff_ruptures       0.016     0.0       5     
reading exposure               0.009     0.0       1     
store source_info              0.004     0.0       1     
prefiltering source model      0.003     0.0       1     
aggregate curves               2.215E-04 0.0       5     
saving probability maps        3.052E-05 0.0       1     
reading site collection        7.153E-06 0.0       1     
============================== ========= ========= ======