Classical Hazard QA Test, Case 12
=================================

============== ===================
checksum32     597_722_647        
date           2020-01-16T05:31:56
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,1)    1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================== ========= ========== ==========
grp_id gsims                                                distances siteparams ruptparams
====== ==================================================== ========= ========== ==========
0      '[SadighEtAl1997]'                                   rrup      vs30       mag rake  
1      '[NRCan15SiteTerm]\ngmpe_name = "BooreAtkinson2008"' rjb       vs30       mag rake  
====== ==================================================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   1            1.00000     
1      1.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
2         1      P    1            0.00249   1.00000   1.00000     
1         0      P    1            0.00145   1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00393  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.00150 NaN     0.00150 0.00150 1      
preclassical       0.00292 0.00111 0.00214 0.00370 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ====================================== ========
task         sent                                   received
SourceReader                                        2.6 KB  
preclassical srcs=2.3 KB params=1.29 KB gsims=920 B 732 B   
============ ====================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43339                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.01365   0.0       1     
total preclassical          0.00584   0.0       2     
store source_info           0.00268   0.0       1     
total SourceReader          0.00150   0.0       1     
splitting/filtering sources 5.312E-04 0.0       2     
aggregate curves            3.912E-04 0.0       2     
=========================== ========= ========= ======