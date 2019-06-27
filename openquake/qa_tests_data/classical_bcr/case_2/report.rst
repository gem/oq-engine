Classical BCR test
==================

============== ===================
checksum32     1,551,058,886      
date           2019-06-24T15:33:20
engine_version 3.6.0-git4b6205639c
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
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight checksum     
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
0      231       A    4     8     414          0.78158   9.00000   604    3,492,789,313
0      229       A    0     4     264          0.35514   3.00000   297    1,348,912,472
0      232       A    8     12    150          0.29438   8.00000   215    2,764,421,915
====== ========= ==== ===== ===== ============ ========= ========= ====== =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.43110   3     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
build_hazard_stats     0.00628 0.00142 0.00322   0.00774 11     
classical              0.13363 0.01948 0.09832   0.16282 11     
classical_split_filter 0.01070 0.01363 1.748E-04 0.03414 14     
read_source_models     0.05002 NaN     0.05002   0.05002 1      
====================== ======= ======= ========= ======= =======

Fastest task
------------
taskno=0, weight=264, duration=0 s, sources="232"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   264     NaN    264 264 1
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
classical              srcs=54.75 KB params=7.08 KB gsims=5.22 KB srcfilter=3.01 KB   31.02 KB
classical_split_filter srcs=54.75 KB params=7.08 KB gsims=5.22 KB srcfilter=3.01 KB   65.85 KB
read_source_models     converter=313 B fnames=110 B                                   3.93 KB 
====================== ============================================================== ========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              1.46992   1.01953   11    
make_contexts                0.63695   0.0       792   
get_poes                     0.54906   0.0       744   
total classical_split_filter 0.14984   0.51172   14    
filtering/splitting sources  0.07507   0.51172   3     
total build_hazard_stats     0.06908   1.00781   11    
read PoEs                    0.05296   1.00781   11    
total read_source_models     0.05002   0.0       1     
building riskinputs          0.02207   0.0       1     
saving statistics            0.00973   0.0       11    
compute stats                0.00851   0.0       11    
managing sources             0.00367   0.0       1     
aggregate curves             0.00346   0.0       14    
store source model           0.00323   0.0       1     
saving probability maps      0.00185   0.0       1     
store source_info            0.00173   0.0       1     
combine pmaps                0.00147   0.0       11    
reading exposure             5.620E-04 0.0       1     
============================ ========= ========= ======