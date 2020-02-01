Classical Hazard QA Test, Case 6
================================

============== ===================
checksum32     2_288_122_263      
date           2020-01-16T05:31:13
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
truncation_level                0.0               
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
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
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.01429   140          140         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    91           0.00570   0.01099   91          
2         0      C    49           0.00477   0.02041   49          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.00477  
S    0.00570  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.11363 NaN       0.11363 0.11363 1      
preclassical       0.00645 7.308E-04 0.00593 0.00697 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader                                             2.96 KB 
preclassical srcs=2.25 KB params=1.29 KB srcfilter=446 B 732 B   
============ =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43307                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.12242   0.0       1     
total SourceReader          0.11363   0.0       1     
total preclassical          0.01290   0.0       2     
store source_info           0.00238   0.0       1     
splitting/filtering sources 6.897E-04 0.0       2     
aggregate curves            3.564E-04 0.0       2     
=========================== ========= ========= ======