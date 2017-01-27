Classical Hazard QA Test, Case 17
=================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_81054.hdf5 Thu Jan 26 14:28:44 2017
engine_version                                 2.3.0-gite807292        
hazardlib_version                              0.23.0-gite1ea7ea       
============================================== ========================

num_sites = 1, sitecol = 762 B

Parameters
----------
=============================== ===============================
calculation_mode                'classical'                    
number_of_logic_tree_samples    5                              
maximum_distance                {'active shallow crust': 200.0}
investigation_time              1000.0                         
ses_per_logic_tree_path         1                              
truncation_level                2.0                            
rupture_mesh_spacing            1.0                            
complex_fault_mesh_spacing      1.0                            
width_of_mfd_bin                1.0                            
area_source_discretization      10.0                           
ground_motion_correlation_model None                           
random_seed                     106                            
master_seed                     0                              
=============================== ===============================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.200  `source_model_1.xml <source_model_1.xml>`_ trivial(1)      1/1             
b2        0.200  `source_model_2.xml <source_model_2.xml>`_ trivial(1)      4/1             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=5)
  0,SadighEtAl1997(): ['<0,b1~b1,w=0.2>']
  1,SadighEtAl1997(): ['<1,b2~b1,w=0.2>', '<2,b2~b1,w=0.2>', '<3,b2~b1,w=0.2>', '<4,b2~b1,w=0.2>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_1.xml 0      Active Shallow Crust 1           39           39          
source_model_2.xml 1      Active Shallow Crust 1           7            7           
================== ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      2    
#eff_ruptures 46   
#tot_ruptures 46   
#tot_weight   4.600
============= =====

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,214       
count_eff_ruptures_num_tasks                2           
count_eff_ruptures_sent.gsims               182         
count_eff_ruptures_sent.monitor             1,984       
count_eff_ruptures_sent.sitecol             1,196       
count_eff_ruptures_sent.sources             2,613       
count_eff_ruptures_tot_received             2,428       
hazard.input_weight                         6.700       
hazard.n_imts                               1           
hazard.n_levels                             3           
hazard.n_realizations                       5           
hazard.n_sites                              1           
hazard.n_sources                            2           
hazard.output_weight                        15          
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         PointSource  39           0.0       1         0        
1      2         PointSource  7            0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       2     
============ ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 8.315E-04 1.180E-06 8.307E-04 8.323E-04 2        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.006     0.0       1     
managing sources                 0.003     0.0       1     
filtering composite source model 0.003     0.0       1     
total count_eff_ruptures         0.002     0.0       2     
store source_info                9.429E-04 0.0       1     
aggregate curves                 5.460E-05 0.0       2     
saving probability maps          4.315E-05 0.0       1     
reading site collection          4.172E-05 0.0       1     
================================ ========= ========= ======