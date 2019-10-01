Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

============== ===================
checksum32     905,885,649        
date           2019-10-01T07:01:14
engine_version 3.8.0-gitbd71c2f960
============== ===================

num_sites = 3, num_levels = 17, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
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
============== ======= =============== ================
smlt_path      weight  gsim_logic_tree num_realizations
============== ======= =============== ================
SM1            0.50000 complex(2,2)    4               
SM2_a3b1       0.25000 simple(2,0)     2               
SM2_a3pt2b0pt8 0.25000 simple(2,0)     2               
============== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============================================== ========= ========== =================
grp_id gsims                                           distances siteparams ruptparams       
====== =============================================== ========= ========== =================
0      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' rjb rrup  vs30 z2pt5 dip mag rake ztor
1      '[Campbell2003]' '[ToroEtAl2002]'               rjb rrup             mag              
2      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' rjb rrup  vs30 z2pt5 dip mag rake ztor
3      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' rjb rrup  vs30 z2pt5 dip mag rake ztor
====== =============================================== ========= ========== =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=16, rlzs=8)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.00000   15           15          
1      3.00000   15           15          
2      3.00000   240          240         
3      3.00000   240          240         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
1         0      P    15           0.00236   3.00000   15           6,348  
2         1      P    15           0.00228   3.00000   15           6,592  
1         2      A    240          0.00222   3.00000   240          108,298
1         3      A    240          0.00155   3.00000   240          154,676
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00377   2     
P    0.00464   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.00903 0.00600   0.00237 0.01402 3      
preclassical       0.00258 4.426E-04 0.00192 0.00288 4      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ ========================================== ========
task         sent                                       received
SourceReader apply_unc=4.4 KB ltmodel=590 B fname=318 B 10.96 KB
preclassical srcs=6.12 KB params=2.74 KB gsims=1.09 KB  1.34 KB 
============ ========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6644              time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.02791  0.0       1     
total SourceReader     0.02709  0.0       3     
total preclassical     0.01033  0.40625   4     
store source_info      0.00242  0.0       1     
aggregate curves       0.00153  0.0       4     
====================== ======== ========= ======