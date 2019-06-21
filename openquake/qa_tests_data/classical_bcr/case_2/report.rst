Classical BCR test
==================

============== ===================
checksum32     1,551,058,886      
date           2019-06-21T09:41:52
engine_version 3.6.0-git17fd0581aa
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

  <RlzsAssoc(size=3, rlzs=3)
  0,'[AkkarBommer2010]': [2]
  0,'[BooreAtkinson2008]': [1]
  0,'[ChiouYoungs2008]': [0]>

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
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
0      231       A    4     8     414          0.77554   9.00000   604   
0      229       A    0     4     264          0.37184   3.00000   297   
0      232       A    8     12    150          0.28872   8.00000   215   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.43610   3     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
build_hazard_stats     0.00664 0.00168 0.00382   0.00892 11     
classical              0.13344 0.01481 0.10843   0.15440 11     
classical_split_filter 0.01007 0.01263 1.535E-04 0.03003 14     
read_source_models     0.05439 NaN     0.05439   0.05439 1      
====================== ======= ======= ========= ======= =======

Fastest task
------------
taskno=1, weight=414, duration=0 s, sources="229"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   414     NaN    414 414 1
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=414, duration=0 s, sources="229"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   414     NaN    414 414 1
======== ======= ====== === === =

Data transfer
-------------
====================== ============================================================== ========
task                   sent                                                           received
build_hazard_stats     pgetter=4.35 KB hstats=2.09 KB N=154 B individual_curves=143 B 7.52 KB 
classical              srcs=54.7 KB params=7.08 KB gsims=5.22 KB srcfilter=3.01 KB    30.7 KB 
classical_split_filter srcs=54.7 KB params=7.08 KB gsims=5.22 KB srcfilter=3.01 KB    65.76 KB
read_source_models     converter=313 B fnames=110 B                                   3.92 KB 
====================== ============================================================== ========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              1.46788   1.02734   11    
make_contexts                0.62541   0.0       792   
get_poes                     0.54146   0.0       744   
total classical_split_filter 0.14104   0.51953   14    
total build_hazard_stats     0.07309   1.50391   11    
filtering/splitting sources  0.06732   0.51953   3     
read PoEs                    0.05992   1.50391   11    
total read_source_models     0.05439   0.0       1     
building riskinputs          0.02202   0.0       1     
saving statistics            0.00853   0.0       11    
compute stats                0.00659   0.0       11    
managing sources             0.00389   0.0       1     
aggregate curves             0.00326   0.0       14    
saving probability maps      0.00199   0.0       1     
store source model           0.00186   0.0       1     
store source_info            0.00180   0.0       1     
combine pmaps                0.00139   0.0       11    
reading exposure             5.484E-04 0.0       1     
============================ ========= ========= ======