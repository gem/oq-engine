Reduced Hazard Italy
====================

============== ===================
checksum32     2_542_535_525      
date           2020-03-13T11:21:24
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 148, num_levels = 30, num_rlzs = 4

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              200.0             
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
amplification           `amplification.csv <amplification.csv>`_                    
exposure                `exposure.xml <exposure.xml>`_                              
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `site_model.csv <site_model.csv>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b11       1.00000 4               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================== ================= ======================= ============================
grp_id gsims                                                                              distances         siteparams              ruptparams                  
====== ================================================================================== ================= ======================= ============================
0      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ================================================================================== ================= ======================= ============================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.06138   2_295        945         
====== ========= ============ ============

Exposure model
--------------
=========== ===
#assets     151
#taxonomies 17 
=========== ===

================= ======= ======= === === ========= ==========
taxonomy          mean    stddev  min max num_sites num_assets
CR/CDN/HBET:1-2   1.00000 0.0     1   1   8         8         
CR/CDM/HBET:1-2   1.00000 0.0     1   1   13        13        
CR/CDM/HBET:3-5   1.00000 0.0     1   1   14        14        
CR/CDN/H:4        1.00000 0.0     1   1   2         2         
MUR/LWAL/HBET:5-8 1.00000 0.0     1   1   6         6         
CR/CDM/HBET:6-8   1.00000 0.0     1   1   3         3         
MUR/LWAL/H:3      1.00000 0.0     1   1   18        18        
CR/CDM/SOS        1.00000 0.0     1   1   10        10        
MUR/LWAL/HBET:1-2 1.00000 0.0     1   1   17        17        
CR/CDN/SOS        1.00000 0.0     1   1   10        10        
W/CDN/HBET:1-3    1.00000 0.0     1   1   14        14        
CR/CDH/HBET:1-2   1.00000 0.0     1   1   11        11        
CR/CDH/HBET:6-8   1.00000 0.0     1   1   3         3         
MUR/LWAL/H:4      1.00000 0.0     1   1   8         8         
CR/CDH/HBET:3-5   1.00000 0.0     1   1   9         9         
S/CDM/HBET:4-8    1.00000 0.0     1   1   2         2         
CR/CDN/H:3        1.00000 0.0     1   1   3         3         
*ALL*             1.02027 0.14140 1   2   148       151       
================= ======= ======= === === ========= ==========

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures
========== ====== ==== ============ ========= ========= ============
AS_HRAS083 0      A    2_295        0.00414   0.06138   945         
========== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00414  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.03104 NaN    0.03104 0.03104 1      
read_source_model  0.02410 NaN    0.02410 0.02410 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ===================================== ========
task              sent                                  received
read_source_model                                       2.77 KB 
preclassical      srcs=2.74 KB params=995 B gsims=487 B 370 B   
================= ===================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66938                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.03576   0.0       1     
total preclassical          0.03104   1.01172   1     
total read_source_model     0.02410   0.0       1     
splitting/filtering sources 0.02305   0.50781   1     
reading exposure            0.00399   0.0       1     
store source_info           0.00216   0.0       1     
aggregate curves            4.091E-04 0.0       1     
=========================== ========= ========= ======