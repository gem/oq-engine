Scenario QA Test, Case 1
========================

============== ===================
checksum32     749,899,809        
date           2019-03-19T10:03:20
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 3, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                1.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     3                 
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job.ini <job.ini>`_                    
rupture_model `rupture_model.xml <rupture_model.xml>`_
============= ========================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1               
========= ======= =============== ================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,'[BooreAtkinson2008]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
============ ====== === ============ ============
source_model grp_id trt eff_ruptures tot_ruptures
============ ====== === ============ ============
scenario     0      *   1            0           
============ ====== === ============ ============

Slowest operations
------------------
========= ======== ========= ======
operation time_sec memory_mb counts
========= ======== ========= ======
========= ======== ========= ======