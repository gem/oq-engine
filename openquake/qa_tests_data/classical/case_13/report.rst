Classical PSHA QA test
======================

============== ===================
checksum32     1_493_198_454      
date           2020-03-13T11:23:01
engine_version 3.9.0-gitfb3ef3a732
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
pointsource_distance            {'default': {}}   
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
========================= ======= ================
smlt_path                 weight  num_realizations
========================= ======= ================
aFault_aPriori_D2.1       0.50000 2               
bFault_stitched_D2.1_Char 0.50000 2               
========================= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

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
66_0      0      X    11           0.00260   1.27273   11          
28_0      0      X    11           0.00244   0.81818   11          
60_1      1      X    11           0.00237   0.18182   11          
70_0      1      X    11           0.00234   1.18182   11          
51_0      1      X    11           0.00227   0.72727   11          
56_1      0      X    11           0.00224   1.90909   11          
117_0     1      X    11           0.00189   1.18182   11          
37_1      0      X    11           0.00186   1.45455   11          
22_1      1      X    11           0.00179   0.45455   11          
85_0      0      X    11           0.00179   1.27273   11          
32_0      1      X    11           0.00178   1.36364   11          
108_1     1      X    11           0.00177   1.54545   11          
41_1      1      X    11           0.00177   1.54545   11          
0_0       0      X    11           0.00176   1.00000   11          
18_1      0      X    11           0.00176   0.81818   11          
13_0      1      X    11           0.00175   0.27273   11          
75_1      0      X    11           0.00146   1.63636   11          
47_0      0      X    11           0.00138   0.81818   11          
99_0      1      X    11           0.00120   1.27273   11          
28_0      1      X    11           2.184E-04 0.45455   11          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
X    0.08006  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00541 0.00136 0.00267 0.00793 21     
read_source_model  1.25558 0.44305 0.94230 1.56886 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model converter=664 B fname=214 B srcfilter=8 B  1.46 MB 
preclassical      srcs=1.75 MB params=18.38 KB gsims=5.58 KB 21.82 KB
================= ========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_67006                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      2.69901  0.0       1     
total read_source_model     2.51116  3.50000   2     
total preclassical          0.11368  1.50391   21    
splitting/filtering sources 0.00593  0.0       21    
aggregate curves            0.00434  0.0       21    
store source_info           0.00379  0.64062   1     
=========================== ======== ========= ======