Classical BCR test
==================

============== ===================
checksum32     973_554_553        
date           2020-03-13T11:20:13
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 11, num_levels = 30, num_rlzs = 3

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
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
ses_seed                        42                
=============================== ==================

Input files
-----------
==================================== ============================================================================
Name                                 File                                                                        
==================================== ============================================================================
exposure                             `exposure_model.xml <exposure_model.xml>`_                                  
gsim_logic_tree                      `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                                
job_ini                              `job.ini <job.ini>`_                                                        
source_model_logic_tree              `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                
structural_vulnerability             `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_  
structural_vulnerability_retrofitted `vulnerability_model_retrofitted.xml <vulnerability_model_retrofitted.xml>`_
==================================== ============================================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 3               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ======================= =================
grp_id gsims                                                         distances   siteparams              ruptparams       
====== ============================================================= =========== ======================= =================
0      '[AkkarBommer2010]' '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ============================================================= =========== ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.47727   828          792         
====== ========= ============ ============

Exposure model
--------------
=========== ==
#assets     11
#taxonomies 4 
=========== ==

========================== ======= ====== === === ========= ==========
taxonomy                   mean    stddev min max num_sites num_assets
Adobe                      1.00000 0.0    1   1   2         2         
Stone-Masonry              1.00000 0.0    1   1   6         6         
Unreinforced-Brick-Masonry 1.00000 NaN    1   1   1         1         
Wood                       1.00000 0.0    1   1   2         2         
*ALL*                      1.00000 0.0    1   1   11        11        
========================== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
231       0      A    414          0.00829   1.68357   414         
229       0      A    264          0.00543   0.89035   228         
232       0      A    150          0.00457   1.80000   150         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01829  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.02710 0.00654 0.01992 0.03272 3      
read_source_model  0.03624 NaN     0.03624 0.03624 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           3.8 KB  
preclassical      srcs=5.94 KB params=2.51 KB gsims=1.12 KB 1.08 KB 
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66858                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.08131   0.58594   3     
splitting/filtering sources 0.05949   0.0       3     
composite source model      0.04505   0.0       1     
total read_source_model     0.03624   0.0       1     
store source_info           0.00196   0.0       1     
aggregate curves            6.738E-04 0.0       3     
reading exposure            5.202E-04 0.0       1     
=========================== ========= ========= ======