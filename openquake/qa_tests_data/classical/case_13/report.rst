Classical PSHA QA test
======================

thinkpad:/home/michele/oqdata/calc_16932.hdf5 updated Wed Aug 24 04:50:42 2016

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
engine_version               '2.1.0-git74bd74a'              
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
======================================== =========
count_eff_ruptures_max_received_per_task 1,448    
count_eff_ruptures_num_tasks             8        
count_eff_ruptures_sent.monitor          8,952    
count_eff_ruptures_sent.rlzs_by_gsim     6,024    
count_eff_ruptures_sent.sitecol          6,664    
count_eff_ruptures_sent.sources          1,634,903
count_eff_ruptures_tot_received          11,583   
hazard.input_weight                      4,686    
hazard.n_imts                            2        
hazard.n_levels                          13       
hazard.n_realizations                    4        
hazard.n_sites                           21       
hazard.n_sources                         426      
hazard.output_weight                     2,184    
hostname                                 thinkpad 
======================================== =========

Slowest sources
---------------
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class              weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
1            76_0      CharacteristicFaultSource 11     1         0.003       0.0        0.0           0.0           0        
1            76_1      CharacteristicFaultSource 11     1         0.003       0.0        0.0           0.0           0        
1            73_1      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            4_1       CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            77_1      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            73_0      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            77_0      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            75_0      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            50_0      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            106_0     CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            74_1      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            74_0      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
0            0_0       CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            75_1      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
0            32_0      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            101_0     CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
0            78_0      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            65_0      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
0            59_1      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
1            80_0      CharacteristicFaultSource 11     1         0.002       0.0        0.0           0.0           0        
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
========================= =========== ========== ============= ============= ========= ======
source_class              filter_time split_time cum_calc_time max_calc_time num_tasks counts
========================= =========== ========== ============= ============= ========= ======
CharacteristicFaultSource 0.500       0.0        0.0           0.0           0         354   
========================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 3.105     0.0       1     
managing sources               0.680     0.0       1     
filtering sources              0.599     0.0       426   
store source_info              0.005     0.0       1     
total count_eff_ruptures       0.002     0.0       8     
reading site collection        2.120E-04 0.0       1     
aggregate curves               1.307E-04 0.0       8     
saving probability maps        5.603E-05 0.0       1     
============================== ========= ========= ======