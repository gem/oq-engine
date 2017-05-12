Classical PSHA-Based Hazard
===========================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_21302.hdf5 Fri May 12 10:45:18 2017
engine_version                                   2.4.0-git59713b5        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

num_sites = 7, sitecol = 1.11 KB

Parameters
----------
=============================== ==================
calculation_mode                'classical_damage'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
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
=============================== ==================

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
source_model.xml 0      Active Shallow Crust 1           1694         1,694       
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== =======================================================================
count_eff_ruptures.received    tot 1.11 KB, max_per_task 1.11 KB                                      
count_eff_ruptures.sent        sources 1.06 KB, monitor 892 B, srcfilter 852 B, gsims 91 B, param 65 B
hazard.input_weight            1,694                                                                  
hazard.n_imts                  1 B                                                                    
hazard.n_levels                8 B                                                                    
hazard.n_realizations          1 B                                                                    
hazard.n_sites                 7 B                                                                    
hazard.n_sources               1 B                                                                    
hazard.output_weight           56                                                                     
hostname                       tstation.gem.lan                                                       
require_epsilons               0 B                                                                    
============================== =======================================================================

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
0      1         SimpleFaultSource 1,694        0.003     7         1        
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.003     1     
================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.004 NaN    0.004 0.004 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.007     0.0       1     
reading exposure                 0.006     0.0       1     
total count_eff_ruptures         0.004     0.0       1     
managing sources                 9.248E-04 0.0       1     
store source_info                5.579E-04 0.0       1     
filtering composite source model 4.816E-05 0.0       1     
saving probability maps          3.028E-05 0.0       1     
aggregate curves                 2.456E-05 0.0       1     
reading site collection          5.960E-06 0.0       1     
================================ ========= ========= ======