Event Based from NonParametric source
=====================================

============== ===================
checksum32     196_267_185        
date           2020-03-13T11:21:21
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 3, num_levels = 7, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 500.0}
investigation_time              50.0              
ses_per_logic_tree_path         2                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      20.0              
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
0      3.00000   4            3.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      N    4            0.00231   3.00000   3.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.00231  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00318 NaN    0.00318 0.00318 1      
read_source_model  0.05277 NaN    0.05277 0.05277 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            14.86 KB
preclassical      srcs=17.42 KB params=670 B srcfilter=223 B 369 B   
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66933                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.06728   0.0       1     
total read_source_model     0.05277   0.0       1     
total preclassical          0.00318   1.21094   1     
store source_info           0.00223   0.0       1     
aggregate curves            2.608E-04 0.0       1     
splitting/filtering sources 2.110E-04 0.0       1     
=========================== ========= ========= ======