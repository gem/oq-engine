Ucerf test
==========

============== ===================
checksum32     87,673,300         
date           2019-05-10T05:07:25
engine_version 3.5.0-gitbaeb4c1e35
============== ===================

num_sites = 155, num_levels = 6, num_rlzs = ?

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
====== =========================================================================== ==== ===== ===== ============ ========= ========= ======
grp_id source_id                                                                   code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== =========================================================================== ==== ===== ===== ============ ========= ========= ======
23     FM3_2/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2      U    0     0     1000         0.0       0.0       0.0   
22     FM3_2/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3      U    0     0     1000         0.0       0.0       0.0   
21     FM3_2/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2      U    0     0     1000         0.0       0.0       0.0   
20     FM3_2/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2 U    0     0     1000         0.0       0.0       0.0   
19     FM3_2/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3 U    0     0     1000         0.0       0.0       0.0   
18     FM3_2/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2 U    0     0     1000         0.0       0.0       0.0   
17     FM3_2/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2       U    0     0     1000         0.0       0.0       0.0   
16     FM3_2/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3       U    0     0     1000         0.0       0.0       0.0   
15     FM3_2/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2       U    0     0     1000         0.0       0.0       0.0   
14     FM3_2/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2  U    0     0     1000         0.0       0.0       0.0   
13     FM3_2/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3  U    0     0     1000         0.0       0.0       0.0   
12     FM3_2/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2  U    0     0     1000         0.0       0.0       0.0   
11     FM3_1/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2      U    0     0     1000         0.0       0.0       0.0   
10     FM3_1/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3      U    0     0     1000         0.0       0.0       0.0   
9      FM3_1/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2      U    0     0     1000         0.0       0.0       0.0   
8      FM3_1/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2 U    0     0     1000         0.0       0.0       0.0   
7      FM3_1/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3 U    0     0     1000         0.0       0.0       0.0   
6      FM3_1/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2 U    0     0     1000         0.0       0.0       0.0   
5      FM3_1/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2       U    0     0     1000         0.0       0.0       0.0   
4      FM3_1/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3       U    0     0     1000         0.0       0.0       0.0   
====== =========================================================================== ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
U    0.0       24    
==== ========= ======

Slowest operations
------------------
========= ======== ========= ======
operation time_sec memory_mb counts
========= ======== ========= ======
========= ======== ========= ======