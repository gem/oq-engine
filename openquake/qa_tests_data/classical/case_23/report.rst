Classical PSHA with NZ NSHM
===========================

gem-tstation:/home/michele/ssd/calc_42013.hdf5 updated Wed Aug 24 08:04:25 2016

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
engine_version               '2.1.0-git46eb8e0'                                                                                                  
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
count_eff_ruptures_max_received_per_task 1,479       
count_eff_ruptures_num_tasks             2           
count_eff_ruptures_sent.monitor          2,314       
count_eff_ruptures_sent.rlzs_by_gsim     1,516       
count_eff_ruptures_sent.sitecol          866         
count_eff_ruptures_sent.sources          495,548     
count_eff_ruptures_tot_received          2,958       
hazard.input_weight                      3.000       
hazard.n_imts                            1           
hazard.n_levels                          29          
hazard.n_realizations                    1           
hazard.n_sites                           1           
hazard.n_sources                         4           
hazard.output_weight                     29          
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class              weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
1            21444     CharacteristicFaultSource 1.000  1         0.002       0.0        0.0           0.0           0        
0            1         PointSource               0.500  1         6.413E-05   0.0        0.0           0.0           0        
0            2         PointSource               0.500  1         4.315E-05   0.0        0.0           0.0           0        
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
========================= =========== ========== ============= ============= ========= ======
source_class              filter_time split_time cum_calc_time max_calc_time num_tasks counts
========================= =========== ========== ============= ============= ========= ======
CharacteristicFaultSource 0.002       0.0        0.0           0.0           0         1     
PointSource               1.073E-04   0.0        0.0           0.0           0         2     
========================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.214     0.0       1     
managing sources               0.008     0.0       1     
store source_info              0.005     0.0       1     
filtering sources              0.003     0.0       4     
total count_eff_ruptures       6.311E-04 0.0       2     
aggregate curves               3.386E-05 0.0       2     
reading site collection        3.290E-05 0.0       1     
saving probability maps        2.503E-05 0.0       1     
============================== ========= ========= ======