Classical BCR test
==================

============== ===================
checksum32     1,551,058,886      
date           2019-07-30T15:03:45
engine_version 3.7.0-git3b3dff46da
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

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 744          828         
================ ====== ==================== ============ ============

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
========= ====== ==== ============ ========= ========= ====== =====
source_id grp_id code num_ruptures calc_time num_sites weight speed
========= ====== ==== ============ ========= ========= ====== =====
231       0      A    414          0.64352   3,562     414    643  
229       0      A    264          0.32906   810       180    547  
232       0      A    150          0.29557   1,218     150    507  
========= ====== ==== ============ ========= ========= ====== =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.26814   3     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ========= ======= ======= =======
operation-duration     mean    stddev    min     max     outputs
build_hazard           0.00609 8.850E-04 0.00473 0.00691 6      
classical_split_filter 0.22384 0.19429   0.04998 0.57233 6      
read_source_models     0.03001 NaN       0.03001 0.03001 1      
====================== ======= ========= ======= ======= =======

Fastest task
------------
taskno=2, weight=150, duration=0 s, sources="232"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   8.12000 NaN    8.12000 8.12000 1
weight   150     NaN    150     150     1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=1, weight=414, duration=0 s, sources="231"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   8.60386 NaN    8.60386 8.60386 1
weight   414     NaN    414     414     1
======== ======= ====== ======= ======= =

Data transfer
-------------
====================== ================================================================================== ========
task                   sent                                                                               received
build_hazard           pgetter=2.39 KB hstats=1.14 KB max_sites_disagg=30 B N=30 B individual_curves=24 B 5.78 KB 
classical_split_filter srcs=5.86 KB params=1.63 KB gsims=1.12 KB srcfilter=660 B                          17.39 KB
read_source_models     converter=314 B fnames=103 B                                                       3.92 KB 
====================== ================================================================================== ========

Slowest operations
------------------
============================ ========= ========= ======
calc_15452                   time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      2.29129   3.76953   1     
total classical_split_filter 1.34301   2.13281   6     
make_contexts                0.47123   0.0       792   
get_poes                     0.43858   0.0       744   
filtering/splitting sources  0.06577   1.82031   3     
total build_hazard           0.03651   1.39062   6     
total read_source_models     0.03001   0.21484   1     
read PoEs                    0.02825   1.39062   6     
building riskinputs          0.02336   0.04297   1     
saving statistics            0.00722   0.0       6     
compute stats                0.00491   0.0       11    
managing sources             0.00234   0.01562   1     
store source_info            0.00196   0.0       1     
saving probability maps      0.00141   0.16016   1     
aggregate curves             0.00138   0.0       6     
combine pmaps                0.00102   0.0       11    
reading exposure             5.081E-04 0.0       1     
============================ ========= ========= ======