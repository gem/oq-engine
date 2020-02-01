Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

============== ===================
checksum32     3_553_734_699      
date           2020-01-16T05:31:49
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         2      A    240          0.05614   3.00000   240         
1         3      A    240          0.05025   3.00000   240         
1         0      P    15           0.00436   3.00000   15          
2         1      P    15           0.00425   3.00000   15          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.10639  
P    0.00862  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.00994 0.00728 0.00155 0.01446 3      
preclassical       0.00851 0.00201 0.00519 0.01150 32     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=4.4 KB ltmodel=590 B fname=318 B  8.8 KB  
preclassical srcs=63.28 KB params=26.44 KB gsims=9.02 KB 11.44 KB
============ =========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43329                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          0.27219  0.0       32    
splitting/filtering sources 0.13029  0.0       32    
composite source model      0.03244  0.0       1     
total SourceReader          0.02983  0.0       3     
aggregate curves            0.00578  0.0       32    
store source_info           0.00254  0.0       1     
=========================== ======== ========= ======