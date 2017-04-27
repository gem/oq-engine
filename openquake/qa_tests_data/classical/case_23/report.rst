Classical PSHA with NZ NSHM
===========================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7615.hdf5 Wed Apr 26 15:55:39 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ======================================================================
Name                    File                                                                  
======================= ======================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                          
job_ini                 `job.ini <job.ini>`_                                                  
source                  `NSHM_source_model-editedbkgd.xml <NSHM_source_model-editedbkgd.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_          
======================= ======================================================================

Composite source model
----------------------
========= ====== ====================================================================== ================ ================
smlt_path weight source_model_file                                                      gsim_logic_tree  num_realizations
========= ====== ====================================================================== ================ ================
b1        1.000  `NSHM_source_model-editedbkgd.xml <NSHM_source_model-editedbkgd.xml>`_ trivial(0,1,0,1) 1/1             
========= ====== ====================================================================== ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ===================
grp_id gsims            distances siteparams ruptparams         
====== ================ ========= ========== ===================
0      McVerry2006Asc() rrup      vs30       rake hypo_depth mag
====== ================ ========= ========== ===================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,McVerry2006Asc(): ['<0,b1~b1_@_@_@,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================================ ====== ==================== =========== ============ ============
source_model                     grp_id trt                  num_sources eff_ruptures tot_ruptures
================================ ====== ==================== =========== ============ ============
NSHM_source_model-editedbkgd.xml 0      Active Shallow Crust 2           40           40          
================================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== ===============================================================================
count_eff_ruptures.received    tot 2.51 KB, max_per_task 1.26 KB                                              
count_eff_ruptures.sent        sources 809.53 KB, monitor 2.07 KB, srcfilter 1.34 KB, gsims 187 B, param 130 B
hazard.input_weight            6.000                                                                          
hazard.n_imts                  1 B                                                                            
hazard.n_levels                29 B                                                                           
hazard.n_realizations          1 B                                                                            
hazard.n_sites                 1 B                                                                            
hazard.n_sources               4 B                                                                            
hazard.output_weight           29                                                                             
hostname                       tstation.gem.lan                                                               
require_epsilons               0 B                                                                            
============================== ===============================================================================

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
1      21444     CharacteristicFaultSource 1            0.0       1         0        
1      21445     CharacteristicFaultSource 1            0.0       1         0        
0      1         PointSource               20           0.0       1         0        
0      2         PointSource               20           0.0       1         0        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.0       2     
PointSource               0.0       2     
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.038 0.003  0.035 0.040 2        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.188     0.0       1     
total count_eff_ruptures         0.075     2.367     2     
filtering composite source model 0.003     0.0       1     
store source_info                5.329E-04 0.0       1     
managing sources                 9.871E-05 0.0       1     
reading site collection          3.719E-05 0.0       1     
aggregate curves                 2.933E-05 0.0       2     
saving probability maps          2.551E-05 0.0       1     
================================ ========= ========= ======