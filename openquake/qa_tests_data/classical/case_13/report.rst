Classical PSHA QA test
======================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_48431.hdf5 Wed Sep  7 16:04:54 2016
engine_version                                 2.1.0-gitfaa2965        
hazardlib_version                              0.21.0-git89bccaf       
============================================== ========================

num_sites = 21, sitecol = 1.62 KB

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         4.0                             
complex_fault_mesh_spacing   4.0                             
width_of_mfd_bin             0.1                             
area_source_discretization   10.0                            
random_seed                  23                              
master_seed                  0                               
sites_per_tile               10000                           
============================ ================================

Input files
-----------
======================= ================================================================
Name                    File                                                            
======================= ================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                    
job_ini                 `job.ini <job.ini>`_                                            
sites                   `qa_sites.csv <qa_sites.csv>`_                                  
source                  `aFault_aPriori_D2.1.xml <aFault_aPriori_D2.1.xml>`_            
source                  `bFault_stitched_D2.1_Char.xml <bFault_stitched_D2.1_Char.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_    
======================= ================================================================

Composite source model
----------------------
========================= ====== ================================================================ =============== ================
smlt_path                 weight source_model_file                                                gsim_logic_tree num_realizations
========================= ====== ================================================================ =============== ================
aFault_aPriori_D2.1       0.500  `aFault_aPriori_D2.1.xml <aFault_aPriori_D2.1.xml>`_             simple(2)       2/2             
bFault_stitched_D2.1_Char 0.500  `bFault_stitched_D2.1_Char.xml <bFault_stitched_D2.1_Char.xml>`_ simple(2)       2/2             
========================= ====== ================================================================ =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
1      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  0,BooreAtkinson2008(): ['<0,aFault_aPriori_D2.1~BooreAtkinson2008,w=0.25>']
  0,ChiouYoungs2008(): ['<1,aFault_aPriori_D2.1~ChiouYoungs2008,w=0.25>']
  1,BooreAtkinson2008(): ['<2,bFault_stitched_D2.1_Char~BooreAtkinson2008,w=0.25>']
  1,ChiouYoungs2008(): ['<3,bFault_stitched_D2.1_Char~ChiouYoungs2008,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== =========== ============ ======
source_model                  grp_id trt                  num_sources eff_ruptures weight
============================= ====== ==================== =========== ============ ======
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 168         1848         1,848 
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 186         2046         2,046 
============================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        354  
#eff_ruptures   3,894
filtered_weight 3,894
=============== =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,375       
count_eff_ruptures_num_tasks             17          
count_eff_ruptures_sent.gsims            2,856       
count_eff_ruptures_sent.monitor          19,686      
count_eff_ruptures_sent.sitecol          14,161      
count_eff_ruptures_sent.sources          1,637,018   
count_eff_ruptures_tot_received          23,375      
hazard.input_weight                      4,686       
hazard.n_imts                            2           
hazard.n_levels                          26          
hazard.n_realizations                    4           
hazard.n_sites                           21          
hazard.n_sources                         426         
hazard.output_weight                     2,184       
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class              weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
0            0_0       CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            92_1      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            49_1      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            42_0      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            96_0      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            56_0      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            99_1      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            73_0      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            82_1      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            52_0      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            74_0      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            59_1      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            69_1      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            4_0       CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            92_0      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            86_0      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            73_1      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            91_1      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            72_1      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
1            76_0      CharacteristicFaultSource 11     0         0.001       0.0        0.0           0.0           0        
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
========================= =========== ========== ============= ============= ========= ======
source_class              filter_time split_time cum_calc_time max_calc_time num_tasks counts
========================= =========== ========== ============= ============= ========= ======
CharacteristicFaultSource 0.371       0.0        0.0           0.0           0         354   
========================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.002 4.502E-04 0.001 0.003 17       
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 2.069     0.0       1     
managing sources               0.510     0.0       1     
filtering sources              0.446     0.0       426   
total count_eff_ruptures       0.042     0.0       17    
aggregate curves               3.605E-04 0.0       17    
reading site collection        1.869E-04 0.0       1     
saving probability maps        3.099E-05 0.0       1     
store source_info              1.001E-05 0.0       1     
============================== ========= ========= ======