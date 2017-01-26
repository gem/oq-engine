Classical PSHA-Based Hazard
===========================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_80536.hdf5 Thu Jan 26 05:24:26 2017
engine_version                                 2.3.0-gitd31dc69        
hazardlib_version                              0.23.0-git4d14bee       
============================================== ========================

num_sites = 7, sitecol = 1.01 KB

Parameters
----------
=============================== ===============================
calculation_mode                'classical_damage'             
number_of_logic_tree_samples    0                              
maximum_distance                {'Active Shallow Crust': 200.0}
investigation_time              50.0                           
ses_per_logic_tree_path         1                              
truncation_level                3.0                            
rupture_mesh_spacing            1.0                            
complex_fault_mesh_spacing      1.0                            
width_of_mfd_bin                0.1                            
area_source_discretization      20.0                           
ground_motion_correlation_model None                           
random_seed                     42                             
master_seed                     0                              
sites_per_tile                  10000                          
=============================== ===============================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
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
0      SadighEtAl1997() rrup      vs30       rake mag  
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
source_model.xml 0      Active Shallow Crust 1           1694         1,694       
================ ====== ==================== =========== ============ ============

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,523       
count_eff_ruptures_num_tasks                10          
count_eff_ruptures_sent.gsims               910         
count_eff_ruptures_sent.monitor             13,010      
count_eff_ruptures_sent.sitecol             7,180       
count_eff_ruptures_sent.sources             11,402      
count_eff_ruptures_tot_received             15,230      
hazard.input_weight                         1,694       
hazard.n_imts                               3           
hazard.n_levels                             24          
hazard.n_realizations                       1           
hazard.n_sites                              7           
hazard.n_sources                            1           
hazard.output_weight                        168         
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
Concrete 1.000 0.0    1   1   2         2         
Steel    1.000 0.0    1   1   2         2         
Wood     1.000 0.0    1   1   3         3         
*ALL*    1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
0      1         SimpleFaultSource 1,694        0.0       7         0        
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.0       1     
================= ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 8.136E-04 6.773E-05 7.229E-04 9.394E-04 10       
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
managing sources                 0.132     0.0       1     
split/filter heavy sources       0.130     0.0       1     
reading composite source model   0.014     0.0       1     
total count_eff_ruptures         0.008     0.0       10    
filtering composite source model 0.003     0.0       1     
reading exposure                 0.003     0.0       1     
store source_info                5.295E-04 0.0       1     
aggregate curves                 1.423E-04 0.0       10    
saving probability maps          2.837E-05 0.0       1     
reading site collection          8.821E-06 0.0       1     
================================ ========= ========= ======