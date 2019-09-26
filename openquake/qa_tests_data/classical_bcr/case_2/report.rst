Classical BCR test
==================

============== ===================
checksum32     1,551,058,886      
date           2019-09-24T15:20:54
engine_version 3.7.0-git749bb363b3
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
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
231       0      A    414          0.65846   3,562     414          628  
229       0      A    264          0.34090   810       180          528  
232       0      A    150          0.26693   1,218     150          561  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.26628   3     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
build_hazard           0.00732 0.00217 0.00354 0.01023 11     
classical_split_filter 0.22413 0.24392 0.03014 0.64785 6      
read_source_models     0.05261 NaN     0.05261 0.05261 1      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ============================================= ========
task                   sent                                          received
build_hazard           pgetter=5.46 KB hstats=2.09 KB N=55 B         7.52 KB 
classical_split_filter srcs=5.88 KB srcfilter=3.29 KB params=1.63 KB 18.29 KB
read_source_models     converter=314 B fnames=110 B                  3.93 KB 
====================== ============================================= ========

Slowest operations
------------------
============================ ========= ========= ======
calc_1706                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical_split_filter 1.34476   0.58984   6     
ClassicalCalculator.run      0.88408   1.25391   1     
make_contexts                0.48463   0.0       792   
computing mean_std           0.28330   0.0       744   
get_poes                     0.14505   0.0       744   
total build_hazard           0.08048   1.50391   11    
filtering/splitting sources  0.07392   0.0       3     
read PoEs                    0.06732   1.50391   11    
total read_source_models     0.05261   0.19141   1     
building riskinputs          0.02134   0.0       1     
saving statistics            0.00851   0.0       11    
compute stats                0.00662   0.0       11    
aggregate curves             0.00294   0.0       6     
store source_info            0.00258   0.0       1     
saving probability maps      0.00176   0.0       1     
combine pmaps                0.00145   0.0       11    
reading exposure             6.220E-04 0.0       1     
managing sources             5.908E-04 0.0       1     
============================ ========= ========= ======