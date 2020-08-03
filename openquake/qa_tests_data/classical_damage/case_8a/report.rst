Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     605_210_054        
date           2020-03-13T11:20:49
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 30, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 2               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================== ========= ========== ==========
grp_id gsims                                  distances siteparams ruptparams
====== ====================================== ========= ========== ==========
0      '[AkkarBommer2010]' '[SadighEtAl1997]' rjb rrup  vs30       mag rake  
====== ====================================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.03112   482          482         
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
Wood     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    482          0.02341   0.03112   482         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.02341  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.02457 NaN    0.02457 0.02457 1      
read_source_model  0.00470 NaN    0.00470 0.00470 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ===================================== ========
task              sent                                  received
read_source_model                                       1.45 KB 
preclassical      srcs=1.38 KB params=856 B gsims=258 B 370 B   
================= ===================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66917                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.02457   1.54297   1     
composite source model      0.01713   0.0       1     
total read_source_model     0.00470   0.0       1     
store source_info           0.00244   0.0       1     
reading exposure            5.267E-04 0.0       1     
aggregate curves            4.716E-04 0.0       1     
splitting/filtering sources 4.594E-04 0.25000   1     
=========================== ========= ========= ======