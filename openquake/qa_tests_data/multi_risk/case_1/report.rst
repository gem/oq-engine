Volcano example
===============

============== ===================
checksum32     3_488_609_606      
date           2020-01-16T05:30:42
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 173, num_levels = 45, num_rlzs = 1

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
pointsource_distance            None        
ground_motion_correlation_model None        
minimum_intensity               {}          
random_seed                     42          
master_seed                     0           
ses_seed                        42          
avg_losses                      True        
=============================== ============

Input files
-----------
====================== ================================================
Name                   File                                            
====================== ================================================
exposure               `exposure_model.xml <exposure_model.xml>`_      
job_ini                `job.ini <job.ini>`_                            
reqv:ASH               `ash_fall.csv <ash_fall.csv>`_                  
reqv:LAHAR             `lahar.csv <lahar.csv>`_                        
reqv:LAVA              `lava_flow.csv <lava_flow.csv>`_                
reqv:PYRO              `pyroclastic_flow.csv <pyroclastic_flow.csv>`_  
structural_consequence `consequence_model.xml <consequence_model.xml>`_
structural_fragility   `fragility_model.xml <fragility_model.xml>`_    
====================== ================================================

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

  <RlzsAssoc(size=1, rlzs=1)>

Exposure model
--------------
=========== ===
#assets     174
#taxonomies 4  
=========== ===

============= ======= ======= === === ========= ==========
taxonomy      mean    stddev  min max num_sites num_assets
Moderate_roof 1.02778 0.16667 1   2   36        37        
Heavy_roof    1.00000 0.0     1   1   35        35        
Weak_roof     1.00000 0.0     1   1   43        43        
Slab_roof     1.00000 0.0     1   1   59        59        
*ALL*         1.00578 0.07603 1   2   173       174       
============= ======= ======= === === ========= ==========

Information about the tasks
---------------------------
Not available

Data transfer
-------------
==== ==== ========
task sent received
==== ==== ========

Slowest operations
------------------
================ ======== ========= ======
calc_43207       time_sec memory_mb counts
================ ======== ========= ======
reading exposure 0.00261  0.0       1     
================ ======== ========= ======