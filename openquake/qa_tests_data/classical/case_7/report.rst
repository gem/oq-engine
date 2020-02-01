Classical Hazard QA Test, Case 7
================================

============== ===================
checksum32     1_870_360_642      
date           2020-01-16T05:31:50
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 2

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
b1        0.70000 trivial(1)      1               
b2        0.30000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.01429   140          140         
1      NaN       91           0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
2         0      C    49           0.00456   0.02041   49          
1         0      S    91           0.00266   0.01099   91          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.00456  
S    0.00266  
==== =========

Duplicated sources
------------------
Found 1 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.08782 0.08523 0.02756 0.14809 2      
preclassical       0.00457 0.00174 0.00334 0.00580 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.33 KB ltmodel=378 B fname=210 B 5.18 KB 
preclassical srcs=2.25 KB params=1.29 KB srcfilter=446 B 737 B   
============ =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43332                  time_sec  memory_mb counts
=========================== ========= ========= ======
total SourceReader          0.17565   0.0       2     
composite source model      0.16720   0.0       1     
total preclassical          0.00914   0.0       2     
store source_info           0.00218   0.0       1     
splitting/filtering sources 6.092E-04 0.0       2     
aggregate curves            5.648E-04 0.0       2     
=========================== ========= ========= ======