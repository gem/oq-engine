Classical BCR test
==================

============== ===================
checksum32     1,551,058,886      
date           2019-10-02T10:07:08
engine_version 3.8.0-git6f03622c6e
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
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
231       0      A    414          0.64856   8.60386   414         
229       0      A    264          0.33121   4.50000   180         
232       0      A    150          0.27085   8.12000   150         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.25062   3     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.04663 NaN     0.04663 0.04663 1      
build_hazard           0.00674 0.00169 0.00376 0.00848 11     
classical_split_filter 0.22236 0.23954 0.03244 0.63913 6      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ========================================= ========
task                   sent                                      received
SourceReader                                                     6.87 KB 
build_hazard           pgetter=5.47 KB hstats=2.09 KB N=55 B     7.52 KB 
classical_split_filter srcs=5.83 KB params=1.63 KB gsims=1.12 KB 18.29 KB
====================== ========================================= ========

Slowest operations
------------------
============================ ========= ========= ======
calc_29401                   time_sec  memory_mb counts
============================ ========= ========= ======
total classical_split_filter 1.33414   0.69141   6     
ClassicalCalculator.run      0.86497   0.82812   1     
make_contexts                0.47558   0.0       792   
computing mean_std           0.28287   0.0       744   
get_poes                     0.14385   0.0       744   
filtering/splitting sources  0.07878   0.51172   3     
total build_hazard           0.07415   1.58594   11    
read PoEs                    0.06138   1.49609   11    
composite source model       0.05814   0.57031   1     
total SourceReader           0.04663   0.06250   1     
building riskinputs          0.02663   0.0       1     
saving statistics            0.00918   0.0       11    
compute stats                0.00623   0.0       11    
aggregate curves             0.00328   0.0       6     
store source_info            0.00248   0.0       1     
saving probability maps      0.00173   0.0       1     
combine pmaps                0.00129   0.0       11    
reading exposure             6.142E-04 0.0       1     
============================ ========= ========= ======