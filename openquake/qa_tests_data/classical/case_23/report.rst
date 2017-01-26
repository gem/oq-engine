Classical PSHA with NZ NSHM
===========================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_81075.hdf5 Thu Jan 26 14:29:40 2017
engine_version                                 2.3.0-gite807292        
hazardlib_version                              0.23.0-gite1ea7ea       
============================================== ========================

num_sites = 1, sitecol = 762 B

Parameters
----------
=============================== ================================================================================================================
calculation_mode                'classical'                                                                                                     
number_of_logic_tree_samples    0                                                                                                               
maximum_distance                {'Active Shallow Crust': 400.0, 'Subduction Intraslab': 400.0, 'Subduction Interface': 400.0, 'Volcanic': 400.0}
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
=============================== ================================================================================================================

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
b1        1.000  `NSHM_source_model-editedbkgd.xml <NSHM_source_model-editedbkgd.xml>`_ trivial(1,0,0,1) 1/1             
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
================================ ====== ==================== =========== ============ ============
source_model                     grp_id trt                  num_sources eff_ruptures tot_ruptures
================================ ====== ==================== =========== ============ ============
NSHM_source_model-editedbkgd.xml 0      Active Shallow Crust 2           40           40          
NSHM_source_model-editedbkgd.xml 1      Subduction Interface 2           2            2           
================================ ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      4    
#eff_ruptures 42   
#tot_ruptures 42   
#tot_weight   6.000
============= =====

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,509       
count_eff_ruptures_num_tasks                2           
count_eff_ruptures_sent.gsims               187         
count_eff_ruptures_sent.monitor             2,574       
count_eff_ruptures_sent.sitecol             1,366       
count_eff_ruptures_sent.sources             828,503     
count_eff_ruptures_tot_received             3,018       
hazard.input_weight                         6.000       
hazard.n_imts                               1           
hazard.n_levels                             29          
hazard.n_realizations                       1           
hazard.n_sites                              1           
hazard.n_sources                            4           
hazard.output_weight                        29          
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
0      1         PointSource               20           0.0       1         0        
0      2         PointSource               20           0.0       1         0        
1      21444     CharacteristicFaultSource 1            0.0       1         0        
1      21445     CharacteristicFaultSource 1            0.0       1         0        
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
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 7.650E-04 1.111E-04 6.864E-04 8.435E-04 2        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.274     0.0       1     
filtering composite source model 0.004     0.0       1     
managing sources                 0.002     0.0       1     
total count_eff_ruptures         0.002     0.0       2     
store source_info                0.001     0.0       1     
aggregate curves                 8.488E-05 0.0       2     
reading site collection          6.652E-05 0.0       1     
saving probability maps          4.959E-05 0.0       1     
================================ ========= ========= ======