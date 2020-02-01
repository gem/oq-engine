Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     3_629_822_399      
date           2020-01-16T05:30:56
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 8, num_rlzs = 2

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
pointsource_distance            None              
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================== ========= ========== ==========
grp_id gsims                                  distances siteparams ruptparams
====== ====================================== ========= ========== ==========
0      '[AkkarBommer2010]' '[SadighEtAl1997]' rjb rrup  vs30       mag rake  
====== ====================================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)>

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
1         0      S    482          0.03512   0.03112   482         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.03512  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00531 NaN    0.00531 0.00531 1      
preclassical       0.03696 NaN    0.03696 0.03696 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ===================================== ========
task         sent                                  received
SourceReader                                       2.4 KB  
preclassical srcs=1.14 KB params=703 B gsims=258 B 366 B   
============ ===================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43250                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.03696   0.0       1     
composite source model      0.01658   0.0       1     
total SourceReader          0.00531   0.0       1     
store source_info           0.00248   0.0       1     
splitting/filtering sources 9.491E-04 0.0       1     
reading exposure            4.683E-04 0.0       1     
aggregate curves            2.520E-04 0.0       1     
=========================== ========= ========= ======