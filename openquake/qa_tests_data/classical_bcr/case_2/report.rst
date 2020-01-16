Classical BCR test
==================

============== ===================
checksum32     685_195_881        
date           2020-01-16T05:30:39
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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
0      7.51344   828          744         
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
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
231       0      A    414          0.64459   8.60386   414         
229       0      A    264          0.34104   4.50000   180         
232       0      A    150          0.25349   8.12000   150         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.23912  
==== =========

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.03972 NaN     0.03972 0.03972 1      
build_hazard           0.00707 0.00210 0.00319 0.00951 11     
classical_split_filter 0.44068 0.21204 0.27335 0.67914 3      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ========================================= ========
task                   sent                                      received
SourceReader                                                     4.79 KB 
classical_split_filter srcs=5.88 KB params=2.06 KB gsims=1.12 KB 9.21 KB 
build_hazard           pgetter=5.47 KB hstats=2.09 KB N=55 B     7.35 KB 
====================== ========================================= ========

Slowest operations
------------------
============================ ========= ========= ======
calc_43192                   time_sec  memory_mb counts
============================ ========= ========= ======
total classical_split_filter 1.32204   0.21875   3     
ClassicalCalculator.run      0.86403   0.60156   1     
make_contexts                0.49782   0.0       792   
iter_ruptures                0.33083   0.0       137   
computing mean_std           0.28672   0.0       744   
splitting/filtering sources  0.07864   0.15625   3     
total build_hazard           0.07780   0.73828   11    
get_poes                     0.06501   0.0       744   
read PoEs                    0.06025   0.73828   11    
composite source model       0.05073   0.45312   1     
total SourceReader           0.03972   0.0       1     
composing pnes               0.02930   0.0       744   
building riskinputs          0.02201   0.0       1     
saving statistics            0.00791   0.0       11    
compute stats                0.00762   0.0       11    
store source_info            0.00196   0.0       1     
combine pmaps                0.00185   0.0       11    
saving probability maps      0.00151   0.0       1     
aggregate curves             0.00124   0.0       3     
reading exposure             6.003E-04 0.0       1     
============================ ========= ========= ======