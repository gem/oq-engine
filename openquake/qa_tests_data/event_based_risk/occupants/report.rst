event based risk
================

============== ===================
checksum32     687,330,760        
date           2019-09-24T15:21:08
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 7, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              10000.0           
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      None              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
occupants_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
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

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            482         
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 1 realization(s) x 1 loss type(s) losses x 8 bytes x 20 tasks = 1.09 KB

Exposure model
--------------
=========== =
#assets     7
#taxonomies 1
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
1         0      S    482          0.05587   7.00000   2.00000      35   
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.05587   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.00818 NaN    0.00818 0.00818 1      
sample_ruptures    0.09005 NaN    0.09005 0.09005 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=306 B fnames=116 B 1.5 KB  
sample_ruptures                                 69.7 KB 
================== ============================ ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1796                time_sec  memory_mb counts
======================== ========= ========= ======
EventBasedCalculator.run 0.18834   0.16016   1     
total sample_ruptures    0.09005   0.16016   1     
saving events            0.02817   0.0       1     
total read_source_models 0.00818   0.0       1     
saving ruptures          0.00275   0.0       1     
store source_info        0.00253   0.0       1     
reading exposure         5.958E-04 0.0       1     
======================== ========= ========= ======