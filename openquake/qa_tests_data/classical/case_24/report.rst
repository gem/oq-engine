Classical PSHA using Area Source
================================

============== ===================
checksum32     1,839,663,514      
date           2019-10-01T06:08:36
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 1, num_levels = 197, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   260          260         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
1         0      A    260          0.00303   1.00000   260          85,929
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00303   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.02888 NaN    0.02888 0.02888 1      
preclassical       0.00457 NaN    0.00457 0.00457 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader                                             3.37 KB 
preclassical params=2.58 KB srcs=1.92 KB srcfilter=223 B 342 B   
============ =========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_23157             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.04606   0.51172   1     
total SourceReader     0.02888   0.0       1     
total preclassical     0.00457   0.0       1     
store source_info      0.00241   0.0       1     
aggregate curves       3.655E-04 0.0       1     
====================== ========= ========= ======