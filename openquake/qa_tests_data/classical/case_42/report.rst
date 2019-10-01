SAM int July 2019 A15, 300km
============================

============== ===================
checksum32     210,861,024        
date           2019-10-01T06:08:55
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 1, num_levels = 15, num_rlzs = 1

Parameters
----------
=============================== ===================
calculation_mode                'preclassical'     
number_of_logic_tree_samples    0                  
maximum_distance                {'default': 1000.0}
investigation_time              1.0                
ses_per_logic_tree_path         1                  
truncation_level                3.0                
rupture_mesh_spacing            20.0               
complex_fault_mesh_spacing      50.0               
width_of_mfd_bin                0.2                
area_source_discretization      None               
ground_motion_correlation_model None               
minimum_intensity               {}                 
random_seed                     23                 
master_seed                     0                  
ses_seed                        42                 
=============================== ===================

Input files
-----------
======================= ================================
Name                    File                            
======================= ================================
gsim_logic_tree         `gmmLT_A15.xml <gmmLT_A15.xml>`_
job_ini                 `job.ini <job.ini>`_            
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_        
======================= ================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,0)    1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================ ========= ============ ==========
grp_id gsims                            distances siteparams   ruptparams
====== ================================ ========= ============ ==========
0      '[AbrahamsonEtAl2015SInterHigh]' rrup      backarc vs30 mag       
====== ================================ ========= ============ ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   1,755        1,755       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
int_2     0      C    1,755        0.01610   1.00000   1,755        109,018
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.01610   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.90535 NaN    0.90535 0.90535 1      
preclassical       0.01637 NaN    0.01637 0.01637 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ========================================== ========
task         sent                                       received
SourceReader                                            77.58 KB
preclassical srcs=34.47 KB params=615 B srcfilter=223 B 342 B   
============ ========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_23181             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.92359   0.0       1     
total SourceReader     0.90535   0.25000   1     
total preclassical     0.01637   0.0       1     
store source_info      0.00218   0.0       1     
aggregate curves       2.065E-04 0.0       1     
====================== ========= ========= ======