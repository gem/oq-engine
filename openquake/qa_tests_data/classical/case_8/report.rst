Classical Hazard QA Test, Case 8
================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_26067.hdf5 Tue Jun  6 14:58:39 2017
engine_version                                   2.5.0-gitb270b98        
hazardlib_version                                0.25.0-git6276f16       
================================================ ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     1066              
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `1.8 1.2 <1.8 1.2>`_                                        
source                  `2.0 1.0 <2.0 1.0>`_                                        
source                  `2.2 0.8 <2.2 0.8>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1_b2     0.300  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b3     0.300  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b4     0.400  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
2      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,SadighEtAl1997(): ['<0,b1_b2~b1,w=0.30000000298023216>']
  1,SadighEtAl1997(): ['<1,b1_b3~b1,w=0.30000000298023216>']
  2,SadighEtAl1997(): ['<2,b1_b4~b1,w=0.3999999940395357>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           3000         3,000       
source_model.xml 1      Active Shallow Crust 1           3000         3,000       
source_model.xml 2      Active Shallow Crust 1           3000         3,000       
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   3    
#sources      3    
#eff_ruptures 9,000
#tot_ruptures 9,000
#tot_weight   0    
============= =====

Informational data
------------------
============================== ==========================================================================
count_eff_ruptures.received    tot 1.7 KB, max_per_task 580 B                                            
count_eff_ruptures.sent        sources 3.46 KB, srcfilter 2 KB, param 1.79 KB, monitor 939 B, gsims 273 B
hazard.input_weight            900                                                                       
hazard.n_imts                  1 B                                                                       
hazard.n_levels                4 B                                                                       
hazard.n_realizations          3 B                                                                       
hazard.n_sites                 1 B                                                                       
hazard.n_sources               3 B                                                                       
hazard.output_weight           4.000                                                                     
hostname                       tstation.gem.lan                                                          
require_epsilons               0 B                                                                       
============================== ==========================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
2      1         PointSource  3,000        1.876E-04 1         1        
0      1         PointSource  3,000        1.242E-04 1         1        
1      1         PointSource  3,000        1.078E-04 1         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  4.196E-04 3     
============ ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 7.559E-04 2.133E-04 5.894E-04 9.964E-04 3        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.017     0.0       1     
prefiltering source model      0.015     0.0       1     
store source_info              0.004     0.0       1     
managing sources               0.003     0.0       1     
total count_eff_ruptures       0.002     0.0       3     
aggregate curves               7.033E-05 0.0       3     
reading site collection        4.554E-05 0.0       1     
saving probability maps        3.219E-05 0.0       1     
============================== ========= ========= ======