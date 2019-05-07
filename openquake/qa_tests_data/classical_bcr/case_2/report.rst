Classical BCR test
==================

============== ===================
checksum32     1,551,058,886      
date           2019-05-03T06:43:27
engine_version 3.5.0-git7a6d15e809
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
=============== ========
#assets         11      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

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
0      231       A    4     8     414          0.72182   697       131   
0      229       A    0     4     264          0.34191   203       50    
0      232       A    8     12    150          0.26830   270       44    
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.33203   3     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
read_source_models     0.04736 NaN     0.04736   0.04736 1      
classical_split_filter 0.02563 0.02851 1.757E-04 0.08748 10     
classical              0.18064 0.02580 0.14164   0.20912 7      
build_hazard_stats     0.00741 0.00181 0.00461   0.00981 11     
====================== ======= ======= ========= ======= =======

Fastest task
------------
taskno=1, weight=414, duration=0 s, sources="229"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   41      NaN    41  41  1
======== ======= ====== === === =

Slowest task
------------
taskno=2, weight=150, duration=0 s, sources="231"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   15      NaN    15  15  1
======== ======= ====== === === =

Data transfer
-------------
====================== =============================================================== ========
task                   sent                                                            received
read_source_models     converter=313 B fnames=110 B                                    3.92 KB 
classical_split_filter srcs=46.48 KB params=5.06 KB gsims=3.73 KB srcfilter=2.13 KB    54.04 KB
classical              srcs=46.48 KB params=5.06 KB gsims=3.73 KB srcfilter=2.13 KB    20.14 KB
build_hazard_stats     pgetter=43.22 KB hstats=2.09 KB N=154 B individual_curves=143 B 7.63 KB 
====================== =============================================================== ========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              1.26450   1.05469   7     
make_contexts                0.58515   0.0       792   
get_poes                     0.52265   0.0       744   
total classical_split_filter 0.25631   0.51172   10    
total build_hazard_stats     0.08155   0.15234   11    
filtering/splitting sources  0.07809   0.51172   3     
combine pmaps                0.06502   0.15234   11    
total read_source_models     0.04736   0.0       1     
building riskinputs          0.02142   0.0       1     
compute stats                0.01256   0.0       11    
saving statistics            0.00852   0.0       11    
managing sources             0.00360   0.0       1     
aggregate curves             0.00253   0.0       10    
store source_info            0.00218   0.0       1     
saving probability maps      0.00190   0.0       1     
store source model           0.00164   0.0       1     
reading exposure             4.935E-04 0.0       1     
============================ ========= ========= ======