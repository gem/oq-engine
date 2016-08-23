Classical PSHA QA test
======================

gem-tstation:/home/michele/ssd/calc_41602.hdf5 updated Tue Aug 23 17:47:02 2016

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
engine_version               '2.1.0-git5b04a6e'              
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
count_eff_ruptures_max_received_per_task 1,444       
count_eff_ruptures_num_tasks             17          
count_eff_ruptures_sent.monitor          18,972      
count_eff_ruptures_sent.rlzs_by_gsim     12,804      
count_eff_ruptures_sent.sitecol          14,161      
count_eff_ruptures_sent.sources          1,635,163   
count_eff_ruptures_tot_received          24,548      
hazard.input_weight                      4,686       
hazard.n_imts                            2           
hazard.n_levels                          13          
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
0            0_0       CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            50_0      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            48_0      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            53_1      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            23_0      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            32_0      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            0_1       CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
1            52_1      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            47_1      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            22_1      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            49_1      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            46_0      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            6_1       CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            11_0      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            12_1      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            26_1      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            30_1      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            14_0      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            55_0      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
0            39_0      CharacteristicFaultSource 11     1         0.001       0.0        0.0           0.0           0        
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
========================= =========== ========== ============= ============= ========= ======
source_class              filter_time split_time cum_calc_time max_calc_time num_tasks counts
========================= =========== ========== ============= ============= ========= ======
CharacteristicFaultSource 0.399       0.0        0.0           0.0           0         354   
========================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.925     0.0       1     
managing sources               0.534     0.0       1     
filtering sources              0.477     0.0       426   
total count_eff_ruptures       0.005     0.0       17    
store source_info              0.004     0.0       1     
reading site collection        3.059E-04 0.0       1     
aggregate curves               2.089E-04 0.0       17    
saving probability maps        2.098E-05 0.0       1     
============================== ========= ========= ======