Hazard Calculation for end-to-end hazard+risk
=============================================

============== ===================
checksum32     2,783,587,006      
date           2017-10-18T18:22:12
engine_version 2.7.0-git16fce00   
============== ===================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              15.0              
ses_per_logic_tree_path         1                 
truncation_level                4.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     1024              
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job_h.ini <job_h.ini>`_                                    
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ simple(4,1)     4/4             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================================================== ========== ========== ==============
grp_id gsims                                                                                    distances  siteparams ruptparams    
====== ======================================================================================== ========== ========== ==============
0      AkkarBommer2010()                                                                        rjb        vs30       mag rake      
1      AtkinsonBoore2003SInter() LinLee2008SInter() YoungsEtAl1997SInter() ZhaoEtAl2006SInter() rhypo rrup vs30       hypo_depth mag
====== ======================================================================================== ========== ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=4)
  0,AkkarBommer2010(): [0 1 2 3]
  1,AtkinsonBoore2003SInter(): [1]
  1,LinLee2008SInter(): [3]
  1,YoungsEtAl1997SInter(): [2]
  1,ZhaoEtAl2006SInter(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           23           23          
source_model.xml 1      Subduction Interface 1           23           23          
================ ====== ==================== =========== ============ ============

============= ==
#TRT models   2 
#sources      2 
#eff_ruptures 46
#tot_ruptures 46
#tot_weight   0 
============= ==

Informational data
------------------
=========================== =============================================================================
count_eff_ruptures.received tot 1.18 KB, max_per_task 608 B                                              
count_eff_ruptures.sent     sources 2.29 KB, param 1.94 KB, srcfilter 1.34 KB, monitor 652 B, gsims 425 B
hazard.input_weight         4.6000000000000005                                                           
hazard.n_imts               1                                                                            
hazard.n_levels             50                                                                           
hazard.n_realizations       4                                                                            
hazard.n_sites              1                                                                            
hazard.n_sources            2                                                                            
hazard.output_weight        50.0                                                                         
hostname                    tstation.gem.lan                                                             
require_epsilons            False                                                                        
=========================== =============================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      B         PointSource  23           1.817E-04 1         1        
0      A         PointSource  23           1.416E-04 1         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  3.233E-04 2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ========= ========= ===== =========
operation-duration mean      stddev    min       max   num_tasks
count_eff_ruptures 8.447E-04 2.222E-04 6.876E-04 0.001 2        
================== ========= ========= ========= ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
store source_info              0.004     0.0       1     
managing sources               0.003     0.0       1     
reading composite source model 0.002     0.0       1     
total count_eff_ruptures       0.002     0.086     2     
prefiltering source model      7.086E-04 0.0       1     
aggregate curves               4.435E-05 0.0       2     
reading site collection        4.387E-05 0.0       1     
saving probability maps        2.933E-05 0.0       1     
============================== ========= ========= ======