North Africa PSHA
=================

============== ===================
checksum32     2_135_452_217      
date           2020-01-16T05:31:53
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 2, num_levels = 133, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     19                
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
sites                   `sites.csv <sites.csv>`_                                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============================= ======= =============== ================
smlt_path                     weight  gsim_logic_tree num_realizations
============================= ======= =============== ================
smoothed_model_m_m0.2_b_e0.0  0.50000 trivial(0,1,0)  1               
smoothed_model_m_m0.2_b_m0.05 0.50000 trivial(0,1,0)  1               
============================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =========== ========= ========== ==========
grp_id gsims       distances siteparams ruptparams
====== =========== ========= ========== ==========
0      '[AvgGMPE]'                                
1      '[AvgGMPE]'                                
====== =========== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.00435   460          460         
1      NaN       460          0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
21        0      M    460          0.00298   0.00435   460         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
M    0.00298  
==== =========

Duplicated sources
------------------
Found 0 unique sources and 1 duplicate sources with multiplicity 2.0: ['21']

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.00536 2.478E-04 0.00519 0.00554 2      
preclassical       0.00468 NaN       0.00468 0.00468 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.57 KB ltmodel=433 B fname=206 B 5.97 KB 
preclassical params=2.09 KB srcs=1.55 KB gsims=632 B     371 B   
============ =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43336                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.02437   0.0       1     
total SourceReader          0.01073   0.0       2     
total preclassical          0.00468   0.0       1     
store source_info           0.00239   0.0       1     
splitting/filtering sources 8.333E-04 0.0       1     
aggregate curves            1.554E-04 0.0       1     
=========================== ========= ========= ======