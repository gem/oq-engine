Classical PSHA with NZ NSHM
===========================

gem-tstation:/home/michele/ssd/calc_40731.hdf5 updated Mon Aug 22 13:03:18 2016

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
engine_version               '2.1.0-git8cbb23e'                                                                                                  
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
====== ==================== ============= ============= ===================
grp_id gsims                distances     siteparams    ruptparams         
====== ==================== ============= ============= ===================
0      ['McVerry2006Asc()'] set(['rrup']) set(['vs30']) hypo_depth rake mag
====== ==================== ============= ============= ===================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,McVerry2006Asc(): ['<0,b1~b1_@_@_@,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================================ ====== ==================== =========== ============ ======
source_model                     grp_id trt                  num_sources eff_ruptures weight
================================ ====== ==================== =========== ============ ======
NSHM_source_model-editedbkgd.xml 0      Active Shallow Crust 2           40           1.000 
================================ ====== ==================== =========== ============ ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 2,310       
classical_num_tasks             2           
classical_sent.monitor          2,212       
classical_sent.rlzs_by_gsim     1,516       
classical_sent.sitecol          866         
classical_sent.sources          495,548     
classical_tot_received          4,152       
hazard.input_weight             3.000       
hazard.n_imts                   1           
hazard.n_levels                 29          
hazard.n_realizations           1           
hazard.n_sites                  1           
hazard.n_sources                4           
hazard.output_weight            29          
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class              weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
0            1         PointSource               0.500  1         6.199E-05   0.0        0.031         0.031         1        
0            2         PointSource               0.500  1         4.315E-05   0.0        0.028         0.028         1        
1            21444     CharacteristicFaultSource 1.000  1         0.002       0.0        0.004         0.004         1        
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
========================= =========== ========== ============= ============= ========= ======
source_class              filter_time split_time cum_calc_time max_calc_time num_tasks counts
========================= =========== ========== ============= ============= ========= ======
CharacteristicFaultSource 0.002       0.0        0.004         0.004         1         1     
PointSource               1.051E-04   0.0        0.059         0.059         2         2     
========================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  0.034 0.036  0.008 0.060 2        
classical.memory_mb 0.0   0.0    0.0   0.0   2        
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.203     0.0       1     
total classical                0.068     0.0       2     
making contexts                0.031     0.0       41    
computing poes                 0.013     0.0       40    
store source_info              0.010     0.0       1     
managing sources               0.008     0.0       1     
filtering sources              0.003     0.0       4     
saving probability maps        0.002     0.0       1     
read poes                      8.979E-04 0.0       1     
aggregate curves               3.600E-05 0.0       2     
reading site collection        3.099E-05 0.0       1     
============================== ========= ========= ======