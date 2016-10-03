Classical PSHA with NZ NSHM
===========================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_54421.hdf5 Tue Sep 27 14:07:16 2016
engine_version                                 2.1.0-git1ca7123        
hazardlib_version                              0.21.0-git9261682       
============================================== ========================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ====================================================================================================================
calculation_mode             'classical'                                                                                                         
number_of_logic_tree_samples 0                                                                                                                   
maximum_distance             {u'Subduction Intraslab': 400.0, u'Subduction Interface': 400.0, u'Volcanic': 400.0, u'Active Shallow Crust': 400.0}
investigation_time           50.0                                                                                                                
ses_per_logic_tree_path      1                                                                                                                   
truncation_level             3.0                                                                                                                 
rupture_mesh_spacing         1.0                                                                                                                 
complex_fault_mesh_spacing   1.0                                                                                                                 
width_of_mfd_bin             0.1                                                                                                                 
area_source_discretization   10.0                                                                                                                
random_seed                  23                                                                                                                  
master_seed                  0                                                                                                                   
sites_per_tile               10000                                                                                                               
============================ ====================================================================================================================

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
====== =================== ========= ========== ===================
grp_id gsims               distances siteparams ruptparams         
====== =================== ========= ========== ===================
0      McVerry2006Asc()    rrup      vs30       hypo_depth rake mag
1      McVerry2006SInter() rrup      vs30       hypo_depth rake mag
====== =================== ========= ========== ===================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,McVerry2006Asc(): ['<0,b1~b1_@_b3_@,w=1.0>']
  1,McVerry2006SInter(): ['<0,b1~b1_@_b3_@,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================================ ====== ==================== =========== ============ ======
source_model                     grp_id trt                  num_sources eff_ruptures weight
================================ ====== ==================== =========== ============ ======
NSHM_source_model-editedbkgd.xml 0      Active Shallow Crust 2           40           1.000 
NSHM_source_model-editedbkgd.xml 1      Subduction Interface 1           1            1.000 
================================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        3    
#eff_ruptures   41   
filtered_weight 2.000
=============== =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,527       
count_eff_ruptures_num_tasks             2           
count_eff_ruptures_sent.gsims            169         
count_eff_ruptures_sent.monitor          2,632       
count_eff_ruptures_sent.sitecol          866         
count_eff_ruptures_sent.sources          495,576     
count_eff_ruptures_tot_received          3,054       
hazard.input_weight                      2.000       
hazard.n_imts                            1           
hazard.n_levels                          29          
hazard.n_realizations                    1           
hazard.n_sites                           1           
hazard.n_sources                         3           
hazard.output_weight                     29          
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ========================= ====== ========= =========
grp_id source_id source_class              weight calc_time num_sites
====== ========= ========================= ====== ========= =========
0      2         PointSource               0.500  0.0       0        
0      1         PointSource               0.500  0.0       0        
1      21444     CharacteristicFaultSource 1.000  0.0       0        
====== ========= ========================= ====== ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.0       1     
PointSource               0.0       2     
========================= ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 8.360E-04 1.472E-04 7.319E-04 9.401E-04 2        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.196     0.0       1     
total count_eff_ruptures       0.002     0.0       2     
managing sources               0.001     0.0       1     
store source_info              3.941E-04 0.0       1     
aggregate curves               3.600E-05 0.0       2     
reading site collection        3.290E-05 0.0       1     
saving probability maps        2.098E-05 0.0       1     
============================== ========= ========= ======