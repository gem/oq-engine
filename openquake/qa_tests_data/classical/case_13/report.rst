Classical PSHA QA test
======================

gem-tstation:/home/michele/ssd/calc_40705.hdf5 updated Mon Aug 22 12:50:47 2016

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
engine_version               '2.1.0-git8cbb23e'              
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
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 186         2002         2,046 
============================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        354  
#eff_ruptures   3,850
filtered_weight 3,894
=============== =====

Informational data
------------------
=============================== ============
classical_max_received_per_task 12,250      
classical_num_tasks             17          
classical_sent.monitor          18,105      
classical_sent.rlzs_by_gsim     12,804      
classical_sent.sitecol          14,161      
classical_sent.sources          1,635,163   
classical_tot_received          193,284     
hazard.input_weight             4,686       
hazard.n_imts                   2           
hazard.n_levels                 13          
hazard.n_realizations           4           
hazard.n_sites                  21          
hazard.n_sources                426         
hazard.output_weight            2,184       
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class              weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
1            112_0     CharacteristicFaultSource 11     1         0.001       0.0        0.458         0.458         1        
0            74_1      CharacteristicFaultSource 11     1         0.001       0.0        0.357         0.357         1        
0            71_0      CharacteristicFaultSource 11     1         0.001       0.0        0.357         0.357         1        
0            32_0      CharacteristicFaultSource 11     1         0.001       0.0        0.339         0.339         1        
0            71_1      CharacteristicFaultSource 11     1         0.001       0.0        0.315         0.315         1        
0            32_1      CharacteristicFaultSource 11     1         0.001       0.0        0.293         0.293         1        
0            28_0      CharacteristicFaultSource 11     1         0.001       0.0        0.285         0.285         1        
1            112_1     CharacteristicFaultSource 11     1         0.001       0.0        0.282         0.282         1        
0            30_0      CharacteristicFaultSource 11     1         0.001       0.0        0.274         0.274         1        
0            77_0      CharacteristicFaultSource 11     1         0.001       0.0        0.273         0.273         1        
0            77_1      CharacteristicFaultSource 11     1         0.001       0.0        0.272         0.272         1        
0            64_0      CharacteristicFaultSource 11     1         0.001       0.0        0.272         0.272         1        
0            28_1      CharacteristicFaultSource 11     1         0.001       0.0        0.266         0.266         1        
0            74_0      CharacteristicFaultSource 11     1         0.001       0.0        0.264         0.264         1        
0            76_0      CharacteristicFaultSource 11     1         0.001       0.0        0.255         0.255         1        
0            72_0      CharacteristicFaultSource 11     1         0.001       0.0        0.250         0.250         1        
0            76_1      CharacteristicFaultSource 11     1         0.001       0.0        0.250         0.250         1        
0            62_0      CharacteristicFaultSource 11     1         0.001       0.0        0.249         0.249         1        
0            62_1      CharacteristicFaultSource 11     1         0.001       0.0        0.249         0.249         1        
0            68_0      CharacteristicFaultSource 11     1         0.001       0.0        0.247         0.247         1        
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
========================= =========== ========== ============= ============= ========= ======
source_class              filter_time split_time cum_calc_time max_calc_time num_tasks counts
========================= =========== ========== ============= ============= ========= ======
CharacteristicFaultSource 0.366       0.0        29            29            354       354   
========================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  1.758 1.074  0.646 4.185 17       
classical.memory_mb 0.862 0.944  0.0   1.945 17       
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                29        1.945     17    
making contexts                26        0.0       3,894 
computing poes                 2.960     0.0       3,850 
reading composite source model 2.186     0.0       1     
managing sources               0.525     0.0       1     
filtering sources              0.441     0.0       426   
store source_info              0.119     0.0       1     
read poes                      0.006     0.0       1     
saving probability maps        0.003     0.0       1     
aggregate curves               0.003     0.0       17    
reading site collection        1.669E-04 0.0       1     
============================== ========= ========= ======