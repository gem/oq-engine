Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     3_002_809_595      
date           2020-01-16T05:30:30
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================= =========== ======================= =================
grp_id gsims                                   distances   siteparams              ruptparams       
====== ======================================= =========== ======================= =================
0      '[AkkarBommer2010]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)>

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
231       0      A    4_185        0.02903   0.34217   4_185       
376       0      A    2_220        0.00745   0.10000   360         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.03648  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       2.08775 NaN     2.08775 2.08775 1      
preclassical       0.16504 0.07664 0.08543 0.39273 20     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ========================================== ========
task         sent                                       received
SourceReader                                            39.97 KB
preclassical srcs=55.33 KB params=15.61 KB gsims=5.2 KB 6.27 KB 
============ ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43189                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          3.30075   2.09766   20    
splitting/filtering sources 2.54527   0.87500   20    
composite source model      2.10398   0.93750   1     
total SourceReader          2.08775   0.83203   1     
store source_info           0.00235   0.0       1     
reading exposure            4.532E-04 0.0       1     
aggregate curves            3.777E-04 0.0       2     
=========================== ========= ========= ======