Classical Hazard QA Test, Case 3
================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_14465.hdf5 Thu Aug 17 11:48:11 2017
checksum32                                       4,051,148,706           
engine_version                                   2.6.0-gitbdd9d17        
================================================ ========================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      0.05              
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
source_model.xml 0      Active Shallow Crust 1           31353        31,353      
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== ==================================================================================
count_eff_ruptures.received    tot 1009.37 KB, max_per_task 65.07 KB                                             
count_eff_ruptures.sent        sources 6.16 MB, srcfilter 10.69 KB, param 9.44 KB, monitor 5.05 KB, gsims 1.42 KB
hazard.input_weight            3135.3                                                                            
hazard.n_imts                  1                                                                                 
hazard.n_levels                3                                                                                 
hazard.n_realizations          1                                                                                 
hazard.n_sites                 1                                                                                 
hazard.n_sources               1                                                                                 
hazard.output_weight           3.0                                                                               
hostname                       tstation.gem.lan                                                                  
require_epsilons               False                                                                             
============================== ==================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         AreaSource   31,353       1.582     1         31,353   
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   1.582     1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.126 0.023  0.071 0.152 16       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               6.106     0.0       1     
reading composite source model 3.705     0.0       1     
total count_eff_ruptures       2.018     4.848     16    
aggregate curves               0.033     0.0       16    
store source_info              0.008     0.0       1     
prefiltering source model      0.001     0.0       1     
reading site collection        5.484E-05 0.0       1     
saving probability maps        5.150E-05 0.0       1     
============================== ========= ========= ======