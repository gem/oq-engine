North Africa PSHA
=================

============== ===================
checksum32     4,156,250,378      
date           2019-10-23T16:26:48
engine_version 3.8.0-git2e0d8e6795
============== ===================

num_sites = 2, num_levels = 133, num_rlzs = 8

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
smoothed_model_m_m0.2_b_e0.0  0.50000 simple(0,4,0)   4               
smoothed_model_m_m0.2_b_m0.05 0.50000 simple(0,4,0)   4               
============================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================================================== =========== ======================= =================
grp_id gsims                                                                                          distances   siteparams              ruptparams       
====== ============================================================================================== =========== ======================= =================
0      '[AkkarEtAlRjb2014]' '[AtkinsonBoore2006Modified2011]' '[ChiouYoungs2014]' '[PezeshkEtAl2011]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[AkkarEtAlRjb2014]' '[AtkinsonBoore2006Modified2011]' '[ChiouYoungs2014]' '[PezeshkEtAl2011]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ============================================================================================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=32, rlzs=8)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.00217   460          460         
1      0.00217   460          460         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
21        0      M    460          0.00147   0.00217   460         
21        1      M    460          0.00145   0.00217   460         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
M    0.00292  
==== =========

Duplicated sources
------------------
Found 0 unique sources and 1 duplicate sources with multiplicity 2.0: ['21']

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.00268 2.647E-05 0.00266 0.00270 2      
preclassical       0.00172 5.226E-06 0.00172 0.00172 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.57 KB ltmodel=433 B fname=206 B 8.35 KB 
preclassical params=3.97 KB srcs=3.06 KB gsims=1.23 KB   684 B   
============ =========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_44552             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.03579   0.0       1     
store source_info      0.01823   0.0       1     
total SourceReader     0.00535   0.0       2     
total preclassical     0.00344   0.0       2     
aggregate curves       4.318E-04 0.0       2     
====================== ========= ========= ======