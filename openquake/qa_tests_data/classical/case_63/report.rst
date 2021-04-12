Classical PSHA that utilises Idini 2017 GSIM with soiltype
==========================================================

============== ===================
checksum32     2_265_841_407      
date           2021-04-07T11:23:52
engine_version 3.12.0             
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'classical'                               
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            5.0                                       
complex_fault_mesh_spacing      5.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      None                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     20                                        
master_seed                     123456789                                 
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `site_model.xml <site_model.xml>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ======================= ====
grp_id gsim                    rlzs
====== ======================= ====
0      '[IdiniEtAl2017SInter]' [0] 
====== ======================= ====

Required parameters per tectonic region type
--------------------------------------------
===== ======================= ========== ============= ==========
et_id gsims                   distances  siteparams    ruptparams
===== ======================= ========== ============= ==========
0     '[IdiniEtAl2017SInter]' rhypo rrup soiltype vs30 mag       
===== ======================= ========== ============= ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         X    9.975E-04 1         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ========= ============
code calc_time num_sites eff_ruptures
==== ========= ========= ============
X    9.975E-04 1         1           
==== ========= ========= ============

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
build_hazard       1      0.00399 nan    0.00399 0.00399
classical          1      0.00299 nan    0.00299 0.00299
preclassical       1      0.0     nan    0.0     0.0    
read_source_model  1      0.02094 nan    0.02094 0.02094
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      3.29 KB 
preclassical           3.21 KB 
classical              1.19 KB 
build_hazard           684 B   
================= ==== ========

Slowest operations
------------------
======================= ========= ========= ======
calc_31, maxmem=0.6 GB  time_sec  memory_mb counts
======================= ========= ========= ======
ClassicalCalculator.run 0.54753   4.10938   1     
importing inputs        0.28723   2.23047   1     
composite source model  0.22540   1.72266   1     
total read_source_model 0.02094   0.37891   1     
saving rup_data         0.01097   0.15234   1     
total build_hazard      0.00399   1.02734   1     
total classical         0.00299   0.08984   1     
read PoEs               0.00199   1.00781   1     
make_contexts           9.975E-04 0.0       1     
compute stats           9.971E-04 0.0       1     
aggregate curves        0.0       0.0       1     
collecting hazard       0.0       0.0       1     
combine pmaps           0.0       0.0       1     
composing pnes          0.0       0.0       1     
computing mean_std      0.0       0.0       1     
get_poes                0.0       0.0       1     
saving probability maps 0.0       0.0       1     
splitting sources       0.0       0.00391   1     
total preclassical      0.0       0.00391   1     
weighting sources       0.0       0.0       1     
======================= ========= ========= ======