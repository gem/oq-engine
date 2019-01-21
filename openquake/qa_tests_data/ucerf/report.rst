Ucerf test
==========

============== ===================
checksum32     87,673,300         
date           2019-01-20T07:37:13
engine_version 3.4.0-git452d0c6835
============== ===================

num_sites = 155, num_levels = 6

Parameters
----------
=============================== ==================
calculation_mode                'ucerf_hazard'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              200.0             
ses_per_logic_tree_path         3                 
truncation_level                None              
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {'default': 0.1}  
random_seed                     1066              
master_seed                     0                 
ses_seed                        1066              
=============================== ==================

Input files
-----------
======================= ====================================================================
Name                    File                                                                
======================= ====================================================================
gsim_logic_tree         `gmpe_logic_tree_ucerf_mean.xml <gmpe_logic_tree_ucerf_mean.xml>`_  
job_ini                 `job.ini <job.ini>`_                                                
sites                   `bay_area.csv <bay_area.csv>`_                                      
source_model            `dummy_ucerf_bg_source_redux.xml <dummy_ucerf_bg_source_redux.xml>`_
source_model_logic_tree `dummy_ucerf_smlt_redux.xml <dummy_ucerf_smlt_redux.xml>`_          
======================= ====================================================================

Slowest sources
---------------
====== =========================================================================== ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id                                                                   code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== =========================================================================== ==== ===== ===== ============ ========= ========== ========= ========= ======
0      FM3_1/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2  U    0     0     1000         0.0       3.791E-04  0.0       5         0.0   
1      FM3_1/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3  U    0     0     1000         0.0       1.645E-04  0.0       5         0.0   
2      FM3_1/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2  U    0     0     1000         0.0       1.478E-04  0.0       5         0.0   
3      FM3_1/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2       U    0     0     1000         0.0       1.442E-04  0.0       5         0.0   
4      FM3_1/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3       U    0     0     1000         0.0       1.419E-04  0.0       5         0.0   
5      FM3_1/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2       U    0     0     1000         0.0       1.407E-04  0.0       5         0.0   
6      FM3_1/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2 U    0     0     1000         0.0       1.407E-04  0.0       5         0.0   
7      FM3_1/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3 U    0     0     1000         0.0       1.419E-04  0.0       5         0.0   
8      FM3_1/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2 U    0     0     1000         0.0       1.442E-04  0.0       5         0.0   
9      FM3_1/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2      U    0     0     1000         0.0       1.431E-04  0.0       5         0.0   
10     FM3_1/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3      U    0     0     1000         0.0       3.242E-04  0.0       5         0.0   
11     FM3_1/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2      U    0     0     1000         0.0       1.705E-04  0.0       5         0.0   
12     FM3_2/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2  U    0     0     1000         0.0       1.538E-04  0.0       5         0.0   
13     FM3_2/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3  U    0     0     1000         0.0       1.526E-04  0.0       5         0.0   
14     FM3_2/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2  U    0     0     1000         0.0       1.454E-04  0.0       5         0.0   
15     FM3_2/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2       U    0     0     1000         0.0       1.490E-04  0.0       5         0.0   
16     FM3_2/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3       U    0     0     1000         0.0       1.478E-04  0.0       5         0.0   
17     FM3_2/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2       U    0     0     1000         0.0       1.502E-04  0.0       5         0.0   
18     FM3_2/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2 U    0     0     1000         0.0       1.490E-04  0.0       5         0.0   
19     FM3_2/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3 U    0     0     1000         0.0       1.490E-04  0.0       5         0.0   
====== =========================================================================== ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
U    0.0       24    
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ==== ======= ======= === =======
operation-duration mean stddev  min     max outputs
split_filter       13   5.71352 6.59830 16  3      
================== ==== ======= ======= === =======

Data transfer
-------------
============ ==================================== =========
task         sent                                 received 
split_filter srcs=17 KB srcfilter=756 B seed=42 B 310.24 KB
============ ==================================== =========

Slowest operations
------------------
================== ======== ========= ======
operation          time_sec memory_mb counts
================== ======== ========= ======
total split_filter 39       16        3     
================== ======== ========= ======