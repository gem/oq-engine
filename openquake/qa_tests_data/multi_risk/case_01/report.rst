Volcano example
===============

============== ====================
checksum32     4_053_279_609       
date           2020-11-02T09:35:33 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 173, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ============
calculation_mode                'multi_risk'
number_of_logic_tree_samples    0           
maximum_distance                None        
investigation_time              None        
ses_per_logic_tree_path         1           
truncation_level                None        
rupture_mesh_spacing            5.0         
complex_fault_mesh_spacing      5.0         
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
====== ============ ====
grp_id gsim         rlzs
====== ============ ====
0      '[FromFile]' [0] 
====== ============ ====

Exposure model
--------------
=========== ===
#assets     174
#taxonomies 4  
=========== ===

============= ========== ======= ====== === === =========
taxonomy      num_assets mean    stddev min max num_sites
Moderate_roof 36         1.02778 15%    1   2   37       
Heavy_roof    35         1.00000 0%     1   1   35       
Weak_roof     43         1.00000 0%     1   1   43       
Slab_roof     59         1.00000 0%     1   1   59       
*ALL*         173        1.00578 7%     1   2   174      
============= ========== ======= ====== === === =========

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
calc_47224       time_sec memory_mb counts
================ ======== ========= ======
importing inputs 0.04431  1.18750   1     
reading exposure 0.00325  0.0       1     
================ ======== ========= ======