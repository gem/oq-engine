Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     3_002_809_595      
date           2020-03-13T11:20:05
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 6, num_levels = 19, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
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
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job_haz.ini <job_haz.ini>`_                                
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 2               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================= =========== ======================= =================
grp_id gsims                                   distances   siteparams              ruptparams       
====== ======================================= =========== ======================= =================
0      '[AkkarBommer2010]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================= =========== ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.32299   91_021       4_545       
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     6
#taxonomies 2
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
W        1.00000 0.0    1   1   5         5         
A        1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   6         6         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
231       0      A    4_185        0.03747   0.34217   4_185       
376       0      A    2_220        0.00411   0.10000   360         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.04158  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.17679 0.08057 0.09567 0.43736 20     
read_source_model  2.23382 NaN     2.23382 2.23382 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            33.06 KB
preclassical      srcs=56.89 KB params=15.12 KB gsims=5.2 KB 6.44 KB 
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66855                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          3.53577   2.14844   20    
splitting/filtering sources 2.69496   0.82812   20    
composite source model      2.25195   0.82812   1     
total read_source_model     2.23382   0.60938   1     
store source_info           0.00207   0.0       1     
reading exposure            4.928E-04 0.0       1     
aggregate curves            4.239E-04 0.0       2     
=========================== ========= ========= ======