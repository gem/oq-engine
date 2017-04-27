Classical Hazard QA Test, Case 25, topographic surface1 (Mt Etna)
=================================================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7595.hdf5 Wed Apr 26 15:54:49 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 6, sitecol = 1.05 KB

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      1.0               
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
sites                   `sites.csv <sites.csv>`_                                    
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
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      TusaLanger2016Rhypo() rhypo     vs30       mag       
====== ===================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,TusaLanger2016Rhypo(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ======== =========== ============ ============
source_model     grp_id trt      num_sources eff_ruptures tot_ruptures
================ ====== ======== =========== ============ ============
source_model.xml 0      Volcanic 1           440          440         
================ ====== ======== =========== ============ ============

Informational data
------------------
============================== ========================================================================
count_eff_ruptures.received    tot 1.05 KB, max_per_task 1.05 KB                                       
count_eff_ruptures.sent        sources 3.78 KB, monitor 851 B, srcfilter 824 B, gsims 101 B, param 65 B
hazard.input_weight            44                                                                      
hazard.n_imts                  1 B                                                                     
hazard.n_levels                3 B                                                                     
hazard.n_realizations          1 B                                                                     
hazard.n_sites                 6 B                                                                     
hazard.n_sources               1 B                                                                     
hazard.output_weight           18                                                                      
hostname                       tstation.gem.lan                                                        
require_epsilons               0 B                                                                     
============================== ========================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         AreaSource   440          0.0       6         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       1     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.264 NaN    0.264 0.264 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         0.264     0.0       1     
reading composite source model   0.009     0.0       1     
filtering composite source model 0.001     0.0       1     
store source_info                9.058E-04 0.0       1     
reading site collection          1.996E-04 0.0       1     
managing sources                 1.094E-04 0.0       1     
saving probability maps          4.196E-05 0.0       1     
aggregate curves                 2.742E-05 0.0       1     
================================ ========= ========= ======