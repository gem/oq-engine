Ucerf test
==========

============== ===================
checksum32     862_700_393        
date           2020-03-13T11:20:36
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 155, num_levels = 6, num_rlzs = 48

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         3                 
truncation_level                None              
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
pointsource_distance            {'default': {}}   
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

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
ltbr0001  0.00625 2               
ltbr0002  0.00625 2               
ltbr0003  0.05000 2               
ltbr0037  0.00625 2               
ltbr0038  0.00625 2               
ltbr0039  0.05000 2               
ltbr0541  0.01875 2               
ltbr0542  0.01875 2               
ltbr0543  0.15000 2               
ltbr0577  0.01875 2               
ltbr0578  0.01875 2               
ltbr0579  0.15000 2               
ltbr0721  0.00625 2               
ltbr0722  0.00625 2               
ltbr0723  0.05000 2               
ltbr0757  0.00625 2               
ltbr0758  0.00625 2               
ltbr0759  0.05000 2               
ltbr1261  0.01875 2               
ltbr1262  0.01875 2               
ltbr1263  0.15000 2               
ltbr1297  0.01875 2               
ltbr1298  0.01875 2               
ltbr1299  0.15000 2               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =======================
grp_id gsims                                     distances   siteparams              ruptparams             
====== ========================================= =========== ======================= =======================
0      '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
1      '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
2      '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
3      '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
4      '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
5      '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
6      '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
7      '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
8      '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
9      '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
10     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
11     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
12     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
13     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
14     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
15     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
16     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
17     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
18     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
19     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
20     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
21     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
22     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
23     '[AbrahamsonSilva2008]' '[BooreEtAl2014]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
====== ========================================= =========== ======================= =======================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.29618   8_560        151_028     
1      0.29517   8_560        62_404      
2      NaN       9_748        0.0         
3      NaN       8_560        0.0         
4      NaN       8_560        0.0         
5      NaN       9_748        0.0         
6      NaN       8_560        0.0         
7      NaN       8_560        0.0         
8      NaN       9_748        0.0         
9      NaN       8_956        0.0         
10     NaN       8_956        0.0         
11     NaN       10_144       0.0         
12     NaN       8_236        0.0         
13     NaN       8_236        0.0         
14     NaN       9_424        0.0         
15     NaN       8_236        0.0         
16     NaN       8_236        0.0         
17     NaN       9_424        0.0         
18     NaN       8_236        0.0         
19     NaN       8_236        0.0         
20     NaN       9_424        0.0         
21     NaN       8_632        0.0         
22     NaN       8_632        0.0         
23     NaN       9_820        0.0         
====== ========= ============ ============

Slowest sources
---------------
================================================================================= ====== ==== ============ ========= ========= ============
source_id                                                                         grp_id code num_ruptures calc_time num_sites eff_ruptures
================================================================================= ====== ==== ============ ========= ========= ============
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_0      0      P    576          1.37907   0.30736   8_560       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_6      0      P    216          1.37857   0.30736   8_560       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_4      0      P    324          1.34754   0.30736   8_560       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3_1      1      P    180          1.28225   0.31945   8_236       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_7      0      P    576          1.26532   0.30736   8_560       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_5      0      P    576          1.26222   0.27000   9_748       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_14     0      P    576          1.26015   0.27929   9_424       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_9      0      P    576          1.24678   0.29377   8_956       
FM3_1/ABM/Shaw09Mod/DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2:0:1000 0      U    1000         1.24610   0.31945   8_236       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3_3      1      P    324          1.23398   0.27929   9_424       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_2      0      P    180          1.23236   0.27000   9_748       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_1      0      P    180          1.23213   0.30736   8_560       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_11     0      P    576          1.22986   0.25946   10_144      
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_15     0      P    576          1.22825   0.31945   8_236       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_8      0      P    576          1.21609   0.27000   9_748       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_12     0      P    576          1.21340   0.31945   8_236       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3_0      1      P    576          1.21321   0.27929   9_424       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU3_4      1      P    324          1.21173   0.30480   8_632       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_3      0      P    324          1.21115   0.30736   8_560       
FM3_1_ABM_Shaw09Mod_DsrUni_CharConst_M5Rate6.5_MMaxOff7.3_NoFix_SpatSeisU2_13     0      P    576          1.21046   0.31945   8_236       
================================================================================= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    28       
U    1.24610  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       1.24751 0.05258 1.19151 1.38103 24     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================== ========
task         sent                                               received
preclassical srcs=352.03 KB params=237.12 KB srcfilter=229.9 KB 8.67 KB 
============ ================================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66907                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          29       18        24    
composite source model      0.31767  0.0       1     
splitting/filtering sources 0.01281  0.0       24    
aggregate curves            0.00546  0.0       24    
store source_info           0.00274  0.0       1     
=========================== ======== ========= ======