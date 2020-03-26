SAM int July 2019 A15, 300km
============================

============== ===================
checksum32     3_450_566_160      
date           2020-03-13T11:22:14
engine_version 3.9.0-gitfb3ef3a732
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
pointsource_distance            {'default': {}}    
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================ ========= ============ ==========
grp_id gsims                            distances siteparams   ruptparams
====== ================================ ========= ============ ==========
0      '[AbrahamsonEtAl2015SInterHigh]' rrup      backarc vs30 mag       
====== ================================ ========= ============ ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.02108   1_755        1_755       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
int_2     0      C    1_755        0.04079   0.02108   1_755       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.04079  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       21      NaN    21      21      1      
read_source_model  0.58848 NaN    0.58848 0.58848 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            34.86 KB
preclassical      srcs=35.14 KB params=736 B srcfilter=223 B 370 B   
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66990                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          21        7.59375   1     
splitting/filtering sources 21        8.09375   1     
composite source model      0.61826   0.0       1     
total read_source_model     0.58848   0.0       1     
store source_info           0.00244   0.0       1     
aggregate curves            4.165E-04 0.0       1     
=========================== ========= ========= ======