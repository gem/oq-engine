Classical PSHA — Area Source
============================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29234.hdf5 Wed Jun 14 10:04:33 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 1, num_imts = 1

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
width_of_mfd_bin                0.2               
area_source_discretization      5.0               
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
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
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           11132        11,132      
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== ================================================================================
count_eff_ruptures.received    tot 12.16 KB, max_per_task 3.07 KB                                              
count_eff_ruptures.sent        sources 99.73 KB, param 2.88 KB, srcfilter 2.67 KB, monitor 1.22 KB, gsims 408 B
hazard.input_weight            1,113                                                                           
hazard.n_imts                  1 B                                                                             
hazard.n_levels                19 B                                                                            
hazard.n_realizations          1 B                                                                             
hazard.n_sites                 1 B                                                                             
hazard.n_sources               1 B                                                                             
hazard.output_weight           19                                                                              
hostname                       tstation.gem.lan                                                                
require_epsilons               0 B                                                                             
============================== ================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         AreaSource   11,132       0.038     1         484      
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.038     1     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.012 0.002  0.009 0.014 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.143     0.0       1     
total count_eff_ruptures       0.049     0.0       4     
reading composite source model 0.042     0.0       1     
store source_info              0.007     0.0       1     
prefiltering source model      0.001     0.0       1     
aggregate curves               0.001     0.0       4     
saving probability maps        5.198E-05 0.0       1     
reading site collection        4.601E-05 0.0       1     
============================== ========= ========= ======