Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     779_146_337        
date           2020-03-13T11:20:58
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 100, num_levels = 1, num_rlzs = 15

Parameters
----------
=============================== =================
calculation_mode                'preclassical'   
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              30.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            5.0              
complex_fault_mesh_spacing      5.0              
width_of_mfd_bin                0.1              
area_source_discretization      18.0             
pointsource_distance            {'default': {}}  
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     42               
master_seed                     0                
ses_seed                        23               
=============================== =================

Input files
-----------
======================= ==============================================================================
Name                    File                                                                          
======================= ==============================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                                          
sites                   `sites.csv <sites.csv>`_                                                      
source_model_logic_tree `combined_logic-tree-source-model.xml <combined_logic-tree-source-model.xml>`_
======================= ==============================================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        0.50000 5               
b2        0.20000 5               
b3        0.30000 5               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================================================== ================= ======================= =================
grp_id gsims                                                                                                      distances         siteparams              ruptparams       
====== ========================================================================================================== ================= ======================= =================
0      '[AkkarBommer2010]' '[Campbell2003SHARE]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ToroEtAl2002SHARE]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[AkkarBommer2010]' '[Campbell2003SHARE]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ToroEtAl2002SHARE]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[AkkarBommer2010]' '[Campbell2003SHARE]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ToroEtAl2002SHARE]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      '[FaccioliEtAl2010]'                                                                                       rrup              vs30                    mag rake         
4      '[FaccioliEtAl2010]'                                                                                       rrup              vs30                    mag rake         
5      '[FaccioliEtAl2010]'                                                                                       rrup              vs30                    mag rake         
====== ========================================================================================================== ================= ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
1      0.36444   4_385        1_693       
3      0.71429   14           14          
5      0.43281   640          640         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
19        1      S    349          0.11960   0.30946   349         
20        1      S    31           0.02626   1.74194   31          
22        1      S    34           0.01961   0.17647   34          
21        1      S    7            0.01005   5.14286   7.00000     
259       1      A    96           0.00314   0.48958   96          
247       1      A    156          0.00303   0.37179   156         
1339      1      A    168          0.00293   0.55357   168         
257       1      A    96           0.00254   0.48958   96          
1         3      A    7            0.00175   0.71429   7.00000     
246       1      A    156          0.00139   0.37179   156         
264       1      A    1_022        9.367E-04 0.08730   126         
263       1      A    1_022        9.105E-04 0.08730   126         
258       1      A    96           8.075E-04 0.48958   96          
249       1      A    384          7.296E-04 0.16667   84          
250       1      A    384          6.962E-04 0.15476   84          
248       1      A    384          6.950E-04 0.16667   84          
330059    5      P    14           1.836E-04 0.42857   14          
330061    5      P    18           1.292E-04 0.27778   18          
2         3      A    7            1.197E-04 0.71429   7.00000     
330045    5      P    22           1.171E-04 0.31818   22          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01969  
P    0.00383  
S    0.17552  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.02725 0.03339 0.00678 0.12063 12     
read_source_model  0.04179 0.05327 0.00504 0.10288 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ============================================ ========
task              sent                                         received
read_source_model converter=1.05 KB fname=353 B srcfilter=12 B 38.7 KB 
preclassical      srcs=52.85 KB params=7.27 KB gsims=6.61 KB   5.89 KB 
================= ============================================ ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66929                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.56560  0.0       1     
total preclassical          0.32705  1.85156   12    
total read_source_model     0.12538  1.01953   3     
splitting/filtering sources 0.09448  0.0       12    
aggregate curves            0.00251  0.0       12    
store source_info           0.00233  0.0       1     
=========================== ======== ========= ======