SAM int July 2019 A15, 300km
============================

============== ===================
checksum32     210,861,024        
date           2019-09-24T15:21:18
engine_version 3.7.0-git749bb363b3
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

Number of ruptures per tectonic region type
-------------------------------------------
============ ====== ==================== ============ ============
source_model grp_id trt                  eff_ruptures tot_ruptures
============ ====== ==================== ============ ============
int_2.xml    0      Subduction Interface 1,755        1,755       
============ ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
int_2     0      C    1,755        0.01822   1.00000   1,755        96,341
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.01822   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.01870 NaN    0.01870 0.01870 1      
read_source_models 0.56676 NaN    0.56676 0.56676 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ========================================== ========
task               sent                                       received
preclassical       srcs=34.48 KB srcfilter=666 B params=615 B 342 B   
read_source_models converter=306 B fnames=100 B               34.89 KB
================== ========================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1828                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.56676   1.90625   1     
total preclassical       0.01870   0.0       1     
store source_info        0.00246   0.0       1     
managing sources         5.472E-04 0.0       1     
aggregate curves         3.188E-04 0.0       1     
======================== ========= ========= ======