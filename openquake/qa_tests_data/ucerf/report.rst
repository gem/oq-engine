Ucerf test
==========

============== ===================
checksum32     3_422_077_956      
date           2020-01-16T05:30:51
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      -0.001    0            1000        
1      -0.001    0            1000        
2      -0.001    0            1000        
3      -0.001    0            1000        
4      -0.001    0            1000        
5      -0.001    0            1000        
6      -0.001    0            1000        
7      -0.001    0            1000        
8      -0.001    0            1000        
9      -0.001    0            1000        
10     -0.001    0            1000        
11     -0.001    0            1000        
12     -0.001    0            1000        
13     -0.001    0            1000        
14     -0.001    0            1000        
15     -0.001    0            1000        
16     -0.001    0            1000        
17     -0.001    0            1000        
18     -0.001    0            1000        
19     -0.001    0            1000        
20     -0.001    0            1000        
21     -0.001    0            1000        
22     -0.001    0            1000        
23     -0.001    0            1000        
====== ========= ============ ============

Slowest sources
---------------
=========================================================================== ====== ==== ============ ========= ========= ============
source_id                                                                   grp_id code num_ruptures calc_time num_sites eff_ruptures
=========================================================================== ====== ==== ============ ========= ========= ============
FM3_2/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2 20     U    0            0.0       -0.001    1000        
FM3_2/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3 19     U    0            0.0       -0.001    1000        
FM3_2/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2 18     U    0            0.0       -0.001    1000        
FM3_2/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2      23     U    0            0.0       -0.001    1000        
FM3_2/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3      22     U    0            0.0       -0.001    1000        
FM3_2/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2      21     U    0            0.0       -0.001    1000        
FM3_2/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2  14     U    0            0.0       -0.001    1000        
FM3_2/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3  13     U    0            0.0       -0.001    1000        
FM3_2/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2  12     U    0            0.0       -0.001    1000        
FM3_2/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2       17     U    0            0.0       -0.001    1000        
FM3_2/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3       16     U    0            0.0       -0.001    1000        
FM3_2/ABM/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2       15     U    0            0.0       -0.001    1000        
FM3_1/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2 8      U    0            0.0       -0.001    1000        
FM3_1/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3 7      U    0            0.0       -0.001    1000        
FM3_1/GEOL/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2 6      U    0            0.0       -0.001    1000        
FM3_1/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2      11     U    0            0.0       -0.001    1000        
FM3_1/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3      10     U    0            0.0       -0.001    1000        
FM3_1/GEOL/HB08/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2      9      U    0            0.0       -0.001    1000        
FM3_1/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.6_NoFix_SpatSeisU2  2      U    0            0.0       -0.001    1000        
FM3_1/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3  1      U    0            0.0       -0.001    1000        
=========================================================================== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
U    0.0      
==== =========

Information about the tasks
---------------------------
Not available

Data transfer
-------------
==== ==== ========
task sent received
==== ==== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_43240             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.02864  0.0       1     
====================== ======== ========= ======