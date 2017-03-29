Classical Hazard QA Test, Case 4
================================

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85564.hdf5 Tue Feb 14 15:42:54 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

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
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                1.0               
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
source_model.xml 0      Active Shallow Crust 1           901          901         
================ ====== ==================== =========== ============ ============

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,281       
count_eff_ruptures_num_tasks                1           
count_eff_ruptures_sent.gsims               91          
count_eff_ruptures_sent.monitor             1,055       
count_eff_ruptures_sent.sources             1,073       
count_eff_ruptures_sent.srcfilter           710         
count_eff_ruptures_tot_received             1,281       
hazard.input_weight                         901         
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
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
0      1         SimpleFaultSource 901          0.0       1         0        
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
================== ==== ====== === === =========
operation-duration mean stddev min max num_tasks
count_eff_ruptures 133  NaN    133 133 1        
================== ==== ====== === === =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         133       23        1     
reading composite source model   0.671     0.0       1     
managing sources                 0.002     0.0       1     
filtering composite source model 0.002     0.0       1     
store source_info                9.887E-04 0.0       1     
saving probability maps          4.101E-05 0.0       1     
reading site collection          3.648E-05 0.0       1     
aggregate curves                 3.195E-05 0.0       1     
================================ ========= ========= ======