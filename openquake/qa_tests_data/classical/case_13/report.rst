Classical PSHA QA test
======================

============== ===================
checksum32     1_493_198_454      
date           2020-01-16T05:31:50
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 21, num_levels = 26, num_rlzs = 4

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
sites                   `qa_sites.csv <qa_sites.csv>`_                              
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========================= ======= =============== ================
smlt_path                 weight  gsim_logic_tree num_realizations
========================= ======= =============== ================
aFault_aPriori_D2.1       0.50000 simple(2)       2               
bFault_stitched_D2.1_Char 0.50000 simple(2)       2               
========================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=4)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.15015   1_980        1_958       
1      0.93939   2_706        2_310       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
13_0      1      X    11           0.00348   0.27273   11          
28_0      0      X    11           0.00294   0.81818   11          
108_1     1      X    11           0.00250   1.54545   11          
117_0     1      X    11           0.00249   1.18182   11          
18_1      0      X    11           0.00246   0.81818   11          
99_0      1      X    11           0.00235   1.27273   11          
70_0      0      X    11           0.00227   1.90909   11          
56_1      0      X    11           0.00203   1.90909   11          
51_0      0      X    11           0.00189   1.54545   11          
66_0      1      X    11           0.00175   1.09091   11          
47_0      1      X    11           0.00172   0.63636   11          
75_1      1      X    11           0.00168   0.90909   11          
60_1      1      X    11           0.00165   0.18182   11          
85_0      1      X    11           0.00158   1.45455   11          
37_1      1      X    11           0.00147   0.63636   11          
32_0      0      X    11           0.00143   1.36364   11          
22_1      0      X    11           0.00140   0.27273   11          
0_0       0      X    11           0.00138   1.00000   11          
7_1       0      X    11           0.00135   0.45455   11          
41_1      1      X    11           0.00119   1.54545   11          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
X    0.08951  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       1.56731 0.48548 1.22402 1.91059 2      
preclassical       0.00599 0.00152 0.00411 0.00901 21     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=8.36 KB ltmodel=434 B fname=228 B 1.76 MB 
preclassical srcs=1.48 MB params=18.89 KB gsims=5.58 KB  23.54 KB
============ =========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43335                  time_sec memory_mb counts
=========================== ======== ========= ======
total SourceReader          3.13461  2.81641   2     
composite source model      1.95734  1.19922   1     
total preclassical          0.12584  0.50391   21    
splitting/filtering sources 0.00695  0.0       21    
aggregate curves            0.00476  0.0       21    
store source_info           0.00340  0.0       1     
=========================== ======== ========= ======