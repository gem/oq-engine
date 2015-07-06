Probabilistic Event-Based Hazard Demo
=====================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200.0      
investigation_time           50.0       
ses_per_logic_tree_path      200        
truncation_level             3.0        
rupture_mesh_spacing         10.0       
complex_fault_mesh_spacing   10.0       
width_of_mfd_bin             0.5        
area_source_discretization   10.0       
random_seed                  1024       
master_seed                  0          
============================ ===========

Input files
-----------
=========================== ===================================================================
Name                        File                                                               
exposure                    demos/ProbabilisticEventBased/exposure_model.xml                   
gsim_logic_tree             demos/ProbabilisticEventBased/gmpe_logic_tree.xml                  
job_ini                     demos/ProbabilisticEventBased/job_hazard.ini                       
nonstructural_vulnerability demos/ProbabilisticEventBased/nonstructural_vulnerability_model.xml
source                      demos/ProbabilisticEventBased/source_model.xml                     
source_model_logic_tree     demos/ProbabilisticEventBased/source_model_logic_tree.xml          
structural_vulnerability    demos/ProbabilisticEventBased/structural_vulnerability_model.xml   
=========================== ===================================================================

Composite source model
----------------------
========= ================= ======== =============== ========= ================ ===========
smlt_path source_model_file num_trts gsim_logic_tree num_gsims num_realizations num_sources
========= ================= ======== =============== ========= ================ ===========
b1        source_model.xml  1        trivial         1         1/1              398        
========= ================= ======== =============== ========= ================ ===========

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b1        Active Shallow Crust 21222       
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
(0,)        [0]         
=========== ============