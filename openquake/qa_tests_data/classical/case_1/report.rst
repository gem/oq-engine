Classical Hazard QA Test, Case 1
================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_21342.hdf5 Fri May 12 10:46:01 2017
engine_version                                   2.4.0-git59713b5        
hazardlib_version                                0.24.0-git0596dd3       
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
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
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
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

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
  0,SadighEtAl1997(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           1            1           
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== =======================================================================
count_eff_ruptures.received    tot 1.16 KB, max_per_task 1.16 KB                                      
count_eff_ruptures.sent        sources 1.12 KB, monitor 947 B, srcfilter 684 B, gsims 91 B, param 65 B
hazard.input_weight            0.100                                                                  
hazard.n_imts                  2 B                                                                    
hazard.n_levels                6 B                                                                    
hazard.n_realizations          1 B                                                                    
hazard.n_sites                 1 B                                                                    
hazard.n_sources               1 B                                                                    
hazard.output_weight           6.000                                                                  
hostname                       tstation.gem.lan                                                       
require_epsilons               0 B                                                                    
============================== =======================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         PointSource  1            2.344E-04 1         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  2.344E-04 1     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.001 NaN    0.001 0.001 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.001     0.0       1     
total count_eff_ruptures         0.001     0.0       1     
managing sources                 7.575E-04 0.0       1     
store source_info                5.047E-04 0.0       1     
filtering composite source model 3.743E-05 0.0       1     
reading site collection          3.433E-05 0.0       1     
saving probability maps          2.337E-05 0.0       1     
aggregate curves                 1.884E-05 0.0       1     
================================ ========= ========= ======