Classical Hazard QA Test, Case 5
================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_81072.hdf5 Thu Jan 26 14:29:39 2017
engine_version                                 2.3.0-gite807292        
hazardlib_version                              0.23.0-gite1ea7ea       
============================================== ========================

num_sites = 1, sitecol = 762 B

Parameters
----------
=============================== ===============================
calculation_mode                'classical'                    
number_of_logic_tree_samples    0                              
maximum_distance                {'active shallow crust': 200.0}
investigation_time              1.0                            
ses_per_logic_tree_path         1                              
truncation_level                0.0                            
rupture_mesh_spacing            0.01                           
complex_fault_mesh_spacing      0.01                           
width_of_mfd_bin                1.0                            
area_source_discretization      10.0                           
ground_motion_correlation_model None                           
random_seed                     1066                           
master_seed                     0                              
=============================== ===============================

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
source_model.xml 0      Active Shallow Crust 1           485          485         
================ ====== ==================== =========== ============ ============

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,214       
count_eff_ruptures_num_tasks                3           
count_eff_ruptures_sent.gsims               273         
count_eff_ruptures_sent.monitor             2,976       
count_eff_ruptures_sent.sitecol             1,794       
count_eff_ruptures_sent.sources             3,513       
count_eff_ruptures_tot_received             3,642       
hazard.input_weight                         1,940       
hazard.n_imts                               1           
hazard.n_levels                             3           
hazard.n_realizations                       1           
hazard.n_sites                              1           
hazard.n_sources                            1           
hazard.output_weight                        3.000       
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
0      1         ComplexFaultSource 485          0.0       1         0        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.0       1     
================== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 7.820E-04 8.599E-05 6.828E-04 8.357E-04 3        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   5.408     0.0       1     
managing sources                 0.006     0.0       1     
split/filter heavy sources       0.005     0.0       1     
total count_eff_ruptures         0.002     0.0       3     
filtering composite source model 0.001     0.0       1     
store source_info                4.883E-04 0.0       1     
aggregate curves                 3.839E-05 0.0       3     
reading site collection          3.147E-05 0.0       1     
saving probability maps          2.265E-05 0.0       1     
================================ ========= ========= ======