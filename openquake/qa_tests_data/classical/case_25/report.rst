Classical Hazard QA Test, Case 25, topographic surface1 (Mt Etna)
=================================================================

============================================ ========================
thinkpad:/home/michele/oqdata/calc_1540.hdf5 Thu Feb 16 05:06:33 2017
engine_version                               2.3.0-gitc9c7394        
hazardlib_version                            0.23.0-git2ce30b9       
============================================ ========================

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
=========================================== ========
count_eff_ruptures_max_received_per_task    1,237   
count_eff_ruptures_num_tasks                1       
count_eff_ruptures_sent.gsims               101     
count_eff_ruptures_sent.monitor             1,011   
count_eff_ruptures_sent.sources             2,032   
count_eff_ruptures_sent.srcfilter           850     
count_eff_ruptures_tot_received             1,237   
hazard.input_weight                         44      
hazard.n_imts                               1       
hazard.n_levels                             3       
hazard.n_realizations                       1       
hazard.n_sites                              6       
hazard.n_sources                            1       
hazard.output_weight                        18      
hostname                                    thinkpad
require_epsilons                            False   
=========================================== ========

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
count_eff_ruptures 0.293 NaN    0.293 0.293 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         0.293     3.930     1     
reading composite source model   0.023     0.0       1     
managing sources                 0.002     0.0       1     
filtering composite source model 0.002     0.0       1     
store source_info                0.001     0.0       1     
reading site collection          9.484E-04 0.0       1     
saving probability maps          6.223E-05 0.0       1     
aggregate curves                 5.984E-05 0.0       1     
================================ ========= ========= ======