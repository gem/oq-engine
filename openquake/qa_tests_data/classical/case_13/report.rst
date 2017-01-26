Classical PSHA QA test
======================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_81058.hdf5 Thu Jan 26 14:28:54 2017
engine_version                                 2.3.0-gite807292        
hazardlib_version                              0.23.0-gite1ea7ea       
============================================== ========================

num_sites = 21, sitecol = 1.64 KB

Parameters
----------
=============================== ===============================
calculation_mode                'classical'                    
number_of_logic_tree_samples    0                              
maximum_distance                {'Active Shallow Crust': 200.0}
investigation_time              50.0                           
ses_per_logic_tree_path         1                              
truncation_level                3.0                            
rupture_mesh_spacing            4.0                            
complex_fault_mesh_spacing      4.0                            
width_of_mfd_bin                0.1                            
area_source_discretization      10.0                           
ground_motion_correlation_model None                           
random_seed                     23                             
master_seed                     0                              
=============================== ===============================

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
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30measured vs30 z1pt0 dip mag ztor rake
1      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30measured vs30 z1pt0 dip mag ztor rake
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
============================= ====== ==================== =========== ============ ============
source_model                  grp_id trt                  num_sources eff_ruptures tot_ruptures
============================= ====== ==================== =========== ============ ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 178         1958         1,958       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 210         2310         2,310       
============================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      388  
#eff_ruptures 4,268
#tot_ruptures 4,268
#tot_weight   4,268
============= =====

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,475       
count_eff_ruptures_num_tasks                22          
count_eff_ruptures_sent.gsims               3,938       
count_eff_ruptures_sent.monitor             27,500      
count_eff_ruptures_sent.sitecol             21,956      
count_eff_ruptures_sent.sources             1,472,237   
count_eff_ruptures_tot_received             32,387      
hazard.input_weight                         4,268       
hazard.n_imts                               2           
hazard.n_levels                             26          
hazard.n_realizations                       4           
hazard.n_sites                              21          
hazard.n_sources                            388         
hazard.output_weight                        2,184       
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
1      66_0      CharacteristicFaultSource 11           0.0       12        0        
1      103_0     CharacteristicFaultSource 11           0.0       14        0        
0      83_0      CharacteristicFaultSource 11           0.0       11        0        
0      48_1      CharacteristicFaultSource 11           0.0       7         0        
0      39_0      CharacteristicFaultSource 11           0.0       9         0        
0      55_0      CharacteristicFaultSource 11           0.0       7         0        
1      12_0      CharacteristicFaultSource 11           0.0       3         0        
1      77_1      CharacteristicFaultSource 11           0.0       13        0        
0      25_1      CharacteristicFaultSource 11           0.0       9         0        
0      20_0      CharacteristicFaultSource 11           0.0       3         0        
0      30_1      CharacteristicFaultSource 11           0.0       13        0        
1      109_1     CharacteristicFaultSource 11           0.0       3         0        
1      81_1      CharacteristicFaultSource 11           0.0       5         0        
0      46_1      CharacteristicFaultSource 11           0.0       14        0        
0      70_0      CharacteristicFaultSource 11           0.0       21        0        
0      37_1      CharacteristicFaultSource 11           0.0       16        0        
1      92_1      CharacteristicFaultSource 11           0.0       8         0        
0      88_0      CharacteristicFaultSource 11           0.0       15        0        
0      41_1      CharacteristicFaultSource 11           0.0       4         0        
1      95_1      CharacteristicFaultSource 11           0.0       15        0        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.0       388   
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.002 2.759E-04 0.001 0.002 22       
================== ===== ========= ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   2.056     0.0       1     
filtering composite source model 0.360     0.0       1     
managing sources                 0.039     0.0       1     
total count_eff_ruptures         0.037     0.250     22    
store source_info                0.003     0.0       1     
aggregate curves                 2.594E-04 0.0       22    
reading site collection          1.986E-04 0.0       1     
saving probability maps          2.337E-05 0.0       1     
================================ ========= ========= ======