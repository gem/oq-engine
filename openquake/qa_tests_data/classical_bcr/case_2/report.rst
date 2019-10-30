Classical BCR test
==================

============== ===================
checksum32     685,195,881        
date           2019-10-23T16:25:50
engine_version 3.8.0-git2e0d8e6795
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
231       0      A    414          1.19921   8.60386   414         
229       0      A    264          0.63253   4.50000   180         
232       0      A    150          0.49176   8.12000   150         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    2.32349  
==== =========

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.07910 NaN     0.07910 0.07910 1      
build_hazard           0.00522 0.00314 0.00300 0.01278 11     
classical_split_filter 0.79880 0.38851 0.50568 1.23946 3      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ========================================= ========
task                   sent                                      received
classical_split_filter srcs=5.83 KB params=1.75 KB gsims=1.12 KB 9.21 KB 
build_hazard           pgetter=5.47 KB hstats=2.09 KB N=55 B     7.52 KB 
====================== ========================================= ========

Slowest operations
------------------
============================ ========= ========= ======
calc_44410                   time_sec  memory_mb counts
============================ ========= ========= ======
total classical_split_filter 2.39640   0.50000   3     
ClassicalCalculator.run      1.54603   0.36719   1     
make_contexts                0.87015   0.0       792   
computing mean_std           0.56043   0.0       744   
get_poes                     0.16877   0.0       744   
composite source model       0.10524   0.0       1     
total SourceReader           0.07910   0.0       1     
filtering/splitting sources  0.06939   0.50000   3     
building riskinputs          0.05810   0.0       1     
total build_hazard           0.05745   1.49609   11    
read PoEs                    0.04054   1.49609   11    
composing pnes               0.02040   0.0       744   
saving statistics            0.01618   0.0       11    
compute stats                0.01312   0.0       11    
store source_info            0.00216   0.0       1     
saving probability maps      0.00156   0.0       1     
combine pmaps                8.323E-04 0.0       11    
aggregate curves             8.056E-04 0.0       3     
reading exposure             5.238E-04 0.0       1     
============================ ========= ========= ======