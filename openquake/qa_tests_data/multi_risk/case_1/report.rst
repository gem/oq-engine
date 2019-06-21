Volcano example
===============

============== ===================
checksum32     480,304,266        
date           2019-06-21T09:41:55
engine_version 3.6.0-git17fd0581aa
============== ===================

num_sites = 172, num_levels = 45, num_rlzs = 1

Parameters
----------
=============================== ============
calculation_mode                'multi_risk'
number_of_logic_tree_samples    0           
maximum_distance                None        
investigation_time              None        
ses_per_logic_tree_path         1           
truncation_level                None        
rupture_mesh_spacing            None        
complex_fault_mesh_spacing      None        
width_of_mfd_bin                None        
area_source_discretization      None        
ground_motion_correlation_model None        
minimum_intensity               {}          
random_seed                     42          
master_seed                     0           
ses_seed                        42          
avg_losses                      True        
=============================== ============

Input files
-----------
====================== =======================================================================================================================================
Name                   File                                                                                                                                   
====================== =======================================================================================================================================
exposure               `exposure_model.xml <exposure_model.xml>`_                                                                                             
job_ini                `job.ini <job.ini>`_                                                                                                                   
multi_peril            `ash_fall.csv <ash_fall.csv>`_ `lava_flow.csv <lava_flow.csv>`_ `lahar.csv <lahar.csv>`_ `pyroclastic_flow.csv <pyroclastic_flow.csv>`_
structural_consequence `consequence_model.xml <consequence_model.xml>`_                                                                                       
structural_fragility   `fragility_model.xml <fragility_model.xml>`_                                                                                           
====================== =======================================================================================================================================

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
  0,'[FromFile]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
============ ====== === ============ ============
source_model grp_id trt eff_ruptures tot_ruptures
============ ====== === ============ ============
scenario     0      *   1            0           
============ ====== === ============ ============

Exposure model
--------------
=========== ===
#assets     173
#taxonomies 4  
=========== ===

============= ======= ======= === === ========= ==========
taxonomy      mean    stddev  min max num_sites num_assets
Moderate_roof 1.02778 0.16667 1   2   36        37        
Heavy_roof    1.00000 0.0     1   1   35        35        
Weak_roof     1.00000 0.0     1   1   43        43        
Slab_roof     1.00000 0.0     1   1   58        58        
*ALL*         1.00581 0.07625 1   2   172       173       
============= ======= ======= === === ========= ==========

Slowest operations
------------------
================ ======== ========= ======
operation        time_sec memory_mb counts
================ ======== ========= ======
reading exposure 0.00317  0.0       1     
================ ======== ========= ======