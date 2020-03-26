Classical PSHA using Area Source
================================

============== ===================
checksum32     1_766_140_051      
date           2020-03-13T11:22:56
engine_version 3.9.0-gitfb3ef3a732
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
pointsource_distance            {'default': {}}   
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.06667   780          780         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    780          0.00537   0.06667   780         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00537  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.01792 NaN    0.01792 0.01792 1      
read_source_model  0.01439 NaN    0.01439 0.01439 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            2.25 KB 
preclassical      params=2.7 KB srcs=1.98 KB srcfilter=223 B 370 B   
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_67001                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.02544   0.0       1     
total preclassical          0.01792   1.68750   1     
total read_source_model     0.01439   0.0       1     
splitting/filtering sources 0.01171   0.0       1     
store source_info           0.00212   0.0       1     
aggregate curves            4.215E-04 0.0       1     
=========================== ========= ========= ======