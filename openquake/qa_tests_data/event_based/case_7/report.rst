Event-based PSHA with logic tree sampling
=========================================

============== ===================
checksum32     1_207_358_898      
date           2020-03-13T11:21:33
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 3, num_levels = 7, num_rlzs = 1000

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    1000              
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         10                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        23                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b11       0.60900 609             
b12       0.39100 391             
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== =================================================================== =========== ============================= =================
grp_id gsims                                                               distances   siteparams                    ruptparams       
====== =================================================================== =========== ============================= =================
0      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
1      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
====== =================================================================== =========== ============================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.25733   2_456        2_456       
1      0.25733   2_456        2_456       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         1      A    2_456        0.03153   0.25733   2_456       
1         0      A    2_456        0.03087   0.25733   2_456       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.06240  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.08681 3.601E-04 0.08656 0.08707 2      
read_source_model  0.05155 4.835E-04 0.05121 0.05189 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model converter=664 B fname=198 B srcfilter=8 B 8.26 KB 
preclassical      srcs=9.65 KB params=1.31 KB gsims=800 B   740 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66946                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.52825  0.0       1     
total preclassical          0.17362  2.04688   2     
splitting/filtering sources 0.10432  0.72266   2     
total read_source_model     0.10310  0.77344   2     
store source_info           0.00219  0.0       1     
aggregate curves            0.00143  0.0       2     
=========================== ======== ========= ======