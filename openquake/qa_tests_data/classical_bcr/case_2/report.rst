Classical BCR test
==================

============== ===================
checksum32     1,551,058,886      
date           2019-10-01T06:32:18
engine_version 3.8.0-git66affb82eb
============== ===================

num_sites = 11, num_levels = 8, num_rlzs = 3

Parameters
----------
=============================== ==================
calculation_mode                'classical_bcr'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.5               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
==================================== ============================================================================
Name                                 File                                                                        
==================================== ============================================================================
exposure                             `exposure_model.xml <exposure_model.xml>`_                                  
gsim_logic_tree                      `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                                
job_ini                              `job.ini <job.ini>`_                                                        
source_model_logic_tree              `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                
structural_vulnerability             `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_  
structural_vulnerability_retrofitted `vulnerability_model_retrofitted.xml <vulnerability_model_retrofitted.xml>`_
==================================== ============================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(3)       3               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ======================= =================
grp_id gsims                                                         distances   siteparams              ruptparams       
====== ============================================================= =========== ======================= =================
0      '[AkkarBommer2010]' '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ============================================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=3)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      5,590     828          744         
====== ========= ============ ============

Exposure model
--------------
=========== ==
#assets     11
#taxonomies 4 
=========== ==

========================== ======= ====== === === ========= ==========
taxonomy                   mean    stddev min max num_sites num_assets
Adobe                      1.00000 0.0    1   1   2         2         
Stone-Masonry              1.00000 0.0    1   1   6         6         
Unreinforced-Brick-Masonry 1.00000 NaN    1   1   1         1         
Wood                       1.00000 0.0    1   1   2         2         
*ALL*                      1.00000 0.0    1   1   11        11        
========================== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
231       0      A    414          0.68198   3,562     414          607  
229       0      A    264          0.35672   810       180          504  
232       0      A    150          0.28513   1,218     150          526  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.32383   3     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.04523 NaN     0.04523 0.04523 1      
build_hazard           0.00590 0.00207 0.00332 0.00911 11     
classical_split_filter 0.23432 0.25328 0.03213 0.67150 6      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ========================================= ========
task                   sent                                      received
SourceReader                                                     6.58 KB 
build_hazard           pgetter=5.46 KB hstats=2.09 KB N=55 B     7.52 KB 
classical_split_filter srcs=5.83 KB params=1.63 KB gsims=1.12 KB 18.29 KB
====================== ========================================= ========

Slowest operations
------------------
============================ ========= ========= ======
calc_6359                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical_split_filter 1.40593   0.82812   6     
ClassicalCalculator.run      0.89363   0.49219   1     
make_contexts                0.50389   0.0       792   
computing mean_std           0.30114   0.0       744   
get_poes                     0.15134   0.0       744   
filtering/splitting sources  0.07753   0.51562   3     
total build_hazard           0.06494   1.49609   11    
composite source model       0.05531   0.49219   1     
read PoEs                    0.05351   1.49609   11    
total SourceReader           0.04523   0.0       1     
building riskinputs          0.02212   0.0       1     
saving statistics            0.00925   0.0       11    
compute stats                0.00578   0.0       11    
aggregate curves             0.00287   0.0       6     
store source_info            0.00232   0.0       1     
saving probability maps      0.00169   0.0       1     
combine pmaps                0.00126   0.0       11    
reading exposure             6.027E-04 0.0       1     
============================ ========= ========= ======