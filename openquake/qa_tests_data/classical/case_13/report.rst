Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2017-10-18T18:22:44
engine_version 2.7.0-git16fce00   
============== ===================

num_sites = 21, num_imts = 2

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
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
=============================== ==================

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
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  0,BooreAtkinson2008(): [0]
  0,ChiouYoungs2008(): [1]
  1,BooreAtkinson2008(): [2]
  1,ChiouYoungs2008(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== =========== ============ ============
source_model                  grp_id trt                  num_sources eff_ruptures tot_ruptures
============================= ====== ==================== =========== ============ ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 168         1,848        1,848       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 186         2,046        2,046       
============================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      354  
#eff_ruptures 3,894
#tot_ruptures 3,894
#tot_weight   0    
============= =====

Informational data
------------------
=========================== ===================================================================================
count_eff_ruptures.received tot 41.48 KB, max_per_task 1.06 KB                                                 
count_eff_ruptures.sent     sources 1.37 MB, srcfilter 66.82 KB, param 46.3 KB, monitor 17.51 KB, gsims 9.61 KB
hazard.input_weight         40216.0                                                                            
hazard.n_imts               2                                                                                  
hazard.n_levels             26                                                                                 
hazard.n_realizations       4                                                                                  
hazard.n_sites              21                                                                                 
hazard.n_sources            354                                                                                
hazard.output_weight        546.0                                                                              
hostname                    tstation.gem.lan                                                                   
require_epsilons            False                                                                              
=========================== ===================================================================================

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
1      15_0      CharacteristicFaultSource 11           0.018     18        1        
0      71_0      CharacteristicFaultSource 11           0.011     18        1        
0      19_1      CharacteristicFaultSource 11           0.010     5         1        
1      82_1      CharacteristicFaultSource 11           0.010     6         1        
1      33_0      CharacteristicFaultSource 11           0.009     14        1        
1      120_0     CharacteristicFaultSource 11           0.007     7         1        
1      119_1     CharacteristicFaultSource 11           0.006     9         1        
1      81_1      CharacteristicFaultSource 11           0.006     4         1        
1      12_0      CharacteristicFaultSource 11           0.006     3         1        
1      76_0      CharacteristicFaultSource 11           0.006     12        1        
1      31_1      CharacteristicFaultSource 11           0.005     12        1        
1      85_0      CharacteristicFaultSource 11           0.004     14        1        
0      19_0      CharacteristicFaultSource 11           0.004     5         1        
0      34_1      CharacteristicFaultSource 11           0.004     17        1        
0      36_1      CharacteristicFaultSource 11           0.004     14        1        
0      32_1      CharacteristicFaultSource 11           0.004     12        1        
0      33_0      CharacteristicFaultSource 11           0.003     16        1        
0      20_0      CharacteristicFaultSource 11           0.003     2         1        
0      33_1      CharacteristicFaultSource 11           0.003     16        1        
0      12_0      CharacteristicFaultSource 11           0.003     15        1        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.846     354   
========================= ========= ======

Duplicated sources
------------------
========= ========= =============
source_id calc_time src_group_ids
========= ========= =============
0_0       0.005     0 1          
0_1       0.004     0 1          
12_0      0.009     0 1          
12_1      0.005     0 1          
13_0      0.006     0 1          
13_1      0.005     0 1          
14_0      0.005     0 1          
14_1      0.005     0 1          
15_0      0.021     0 1          
15_1      0.005     0 1          
1_0       0.005     0 1          
1_1       0.005     0 1          
2_0       0.005     0 1          
2_1       0.005     0 1          
30_0      0.005     0 1          
30_1      0.005     0 1          
31_0      0.005     0 1          
31_1      0.007     0 1          
32_0      0.005     0 1          
32_1      0.005     0 1          
33_0      0.013     0 1          
33_1      0.005     0 1          
34_0      0.005     0 1          
34_1      0.005     0 1          
35_0      0.005     0 1          
35_1      0.005     0 1          
36_0      0.005     0 1          
36_1      0.005     0 1          
38_0      0.005     0 1          
38_1      0.005     0 1          
39_0      0.005     0 1          
39_1      0.005     0 1          
41_0      0.004     0 1          
41_1      0.004     0 1          
42_0      0.004     0 1          
42_1      0.004     0 1          
43_0      0.004     0 1          
43_1      0.004     0 1          
44_0      0.004     0 1          
44_1      0.004     0 1          
45_0      0.004     0 1          
45_1      0.004     0 1          
46_0      0.004     0 1          
46_1      0.006     0 1          
47_0      0.006     0 1          
47_1      0.006     0 1          
48_0      0.006     0 1          
48_1      0.005     0 1          
49_0      0.005     0 1          
49_1      0.005     0 1          
4_0       0.005     0 1          
4_1       0.005     0 1          
50_0      0.005     0 1          
50_1      0.004     0 1          
51_0      0.005     0 1          
51_1      0.005     0 1          
52_0      0.003     0 1          
52_1      0.003     0 1          
53_0      0.003     0 1          
53_1      0.003     0 1          
54_0      0.003     0 1          
54_1      0.003     0 1          
55_0      0.003     0 1          
55_1      0.003     0 1          
56_0      0.004     0 1          
56_1      0.004     0 1          
57_0      0.004     0 1          
57_1      0.004     0 1          
58_0      0.004     0 1          
58_1      0.004     0 1          
59_0      0.004     0 1          
59_1      0.004     0 1          
60_0      0.004     0 1          
60_1      0.004     0 1          
65_0      0.004     0 1          
65_1      0.004     0 1          
66_0      0.005     0 1          
66_1      0.005     0 1          
67_0      0.004     0 1          
67_1      0.004     0 1          
68_0      0.004     0 1          
68_1      0.004     0 1          
69_0      0.005     0 1          
69_1      0.005     0 1          
70_0      0.004     0 1          
70_1      0.005     0 1          
71_0      0.013     0 1          
71_1      0.003     0 1          
72_0      0.003     0 1          
72_1      0.004     0 1          
73_0      0.004     0 1          
73_1      0.004     0 1          
74_0      0.004     0 1          
74_1      0.004     0 1          
75_0      0.004     0 1          
75_1      0.005     0 1          
76_0      0.008     0 1          
76_1      0.004     0 1          
77_0      0.004     0 1          
77_1      0.004     0 1          
78_0      0.004     0 1          
78_1      0.004     0 1          
79_0      0.004     0 1          
79_1      0.005     0 1          
80_0      0.005     0 1          
80_1      0.005     0 1          
81_0      0.005     0 1          
81_1      0.009     0 1          
82_0      0.004     0 1          
82_1      0.012     0 1          
83_0      0.004     0 1          
83_1      0.004     0 1          
84_0      0.004     0 1          
84_1      0.004     0 1          
85_0      0.007     0 1          
85_1      0.004     0 1          
86_0      0.004     0 1          
86_1      0.004     0 1          
87_0      0.004     0 1          
87_1      0.004     0 1          
88_0      0.004     0 1          
88_1      0.004     0 1          
89_0      0.004     0 1          
89_1      0.004     0 1          
========= ========= =============
Sources with the same ID but different parameters

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.016 0.008  0.005 0.049 55       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.928     0.0       1     
total count_eff_ruptures       0.889     0.0       55    
prefiltering source model      0.572     0.0       1     
managing sources               0.075     0.0       1     
store source_info              0.007     0.0       1     
aggregate curves               0.002     0.0       55    
reading site collection        2.389E-04 0.0       1     
saving probability maps        3.099E-05 0.0       1     
============================== ========= ========= ======