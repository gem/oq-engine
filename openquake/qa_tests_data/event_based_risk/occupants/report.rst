event based risk
================

============== ===================
checksum32     687_330_760        
date           2020-01-16T05:31:06
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.50000   482          2.00000     
====== ========= ============ ============

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
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    482          0.04446   3.50000   2.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.04446  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00491 NaN    0.00491 0.00491 1      
sample_ruptures    0.09132 NaN    0.09132 0.09132 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
=============== ==== ========
task            sent received
SourceReader         2.4 KB  
sample_ruptures      69.7 KB 
=============== ==== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_43287               time_sec  memory_mb counts
======================== ========= ========= ======
EventBasedCalculator.run 0.17443   0.0       1     
total sample_ruptures    0.09132   0.0       1     
saving events            0.02687   0.0       1     
composite source model   0.01452   0.0       1     
total SourceReader       0.00491   0.0       1     
saving ruptures          0.00220   0.0       1     
store source_info        0.00200   0.0       1     
reading exposure         5.925E-04 0.0       1     
======================== ========= ========= ======