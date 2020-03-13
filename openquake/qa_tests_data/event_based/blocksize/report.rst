QA test for blocksize independence (hazard)
===========================================

============== ===================
checksum32     62_194_572         
date           2020-03-13T11:20:56
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 4, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.5               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1024              
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
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== =========== ======================= =================
grp_id gsims               distances   siteparams              ruptparams       
====== =================== =========== ======================= =================
0      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================== =========== ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.34095   5_572        2_625       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    1_752        0.03211   0.33333   1_752       
2         0      A    582          0.01201   0.33333   582         
3         0      A    440          0.00593   0.40000   285         
9         0      A    222          2.129E-04 0.50000   6.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.05027  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.08658 0.04384 0.03845 0.13889 9      
read_source_model  0.47816 NaN     0.47816 0.47816 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ============================================= ========
task              sent                                          received
read_source_model                                               9.19 KB 
preclassical      srcs=18.5 KB params=5.68 KB srcfilter=1.96 KB 3.03 KB 
================= ============================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66927                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.77924   0.60938   9     
splitting/filtering sources 0.61268   0.0       9     
composite source model      0.48904   0.0       1     
total read_source_model     0.47816   0.0       1     
store source_info           0.00258   0.0       1     
aggregate curves            8.328E-04 0.0       4     
=========================== ========= ========= ======