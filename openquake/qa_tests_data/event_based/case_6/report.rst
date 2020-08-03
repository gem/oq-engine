Event-based PSHA producing hazard curves only
=============================================

============== ===================
checksum32     3_503_747_674      
date           2020-03-13T11:20:56
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 5, num_rlzs = 6

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         30                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        23                
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b11       0.60000 3               
b12       0.40000 3               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== =================================================================== =========== ============================= =================
grp_id gsims                                                               distances   siteparams                    ruptparams       
====== =================================================================== =========== ============================= =================
0      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
1      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
====== =================================================================== =========== ============================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.12500   2_456        2_456       
1      0.12500   2_456        2_456       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         1      A    2_456        0.02740   0.12500   2_456       
1         0      A    2_456        0.02690   0.12500   2_456       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.05430  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.08367 0.00133   0.08273 0.08460 2      
read_source_model  0.06458 5.653E-04 0.06418 0.06498 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model converter=664 B fname=198 B srcfilter=8 B 8.26 KB 
preclassical      srcs=9.62 KB params=1.28 KB gsims=800 B   740 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66928                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.16733   1.88281   2     
composite source model      0.13114   0.01953   1     
total read_source_model     0.12916   0.0       2     
splitting/filtering sources 0.10669   0.67969   2     
store source_info           0.00248   0.0       1     
aggregate curves            6.897E-04 0.0       2     
=========================== ========= ========= ======