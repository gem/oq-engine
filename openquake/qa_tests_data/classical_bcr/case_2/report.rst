Classical BCR test
==================

============== ===================
checksum32     1,551,058,886      
date           2019-02-03T09:37:32
engine_version 3.4.0-gite8c42e513a
============== ===================

num_sites = 11, num_levels = 8

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
====== ======================================================= =========== ======================= =================
grp_id gsims                                                   distances   siteparams              ruptparams       
====== ======================================================= =========== ======================= =================
0      AkkarBommer2010() BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,AkkarBommer2010(): [2]
  0,BooreAtkinson2008(): [1]
  0,ChiouYoungs2008(): [0]>

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
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      231       A    4     8     414          0.58939   0.95761    697       69        131   
0      229       A    0     4     264          0.28420   0.39498    203       38        50    
0      232       A    8     12    150          0.21909   0.22312    270       30        44    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.09268   3     
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.03957 NaN       0.03957 0.03957 1      
split_filter       0.04758 NaN       0.04758 0.04758 1      
classical          0.36816 0.18726   0.15312 0.49535 3      
build_hazard_stats 0.00587 3.544E-04 0.00546 0.00638 11     
================== ======= ========= ======= ======= =======

Fastest task
------------
taskno=2, weight=29, duration=0 s, sources="231 232"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   8.50000 1.14708 7       11      20
weight   1.45476 0.09554 1.32288 1.65831 20
======== ======= ======= ======= ======= ==

Slowest task
------------
taskno=0, weight=98, duration=0 s, sources="232"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   7.48387 3.30296 1       11      62
weight   1.58699 0.42254 0.60000 1.98997 62
======== ======= ======= ======= ======= ==

Data transfer
-------------
================== ========================================================= ========
task               sent                                                      received
read_source_models converter=313 B fnames=110 B                              3.92 KB 
split_filter       srcs=3.55 KB srcfilter=253 B seed=14 B                    36.99 KB
classical          group=38.04 KB param=1.48 KB gsims=924 B src_filter=660 B 9.47 KB 
build_hazard_stats pgetter=37.68 KB hstats=2.16 KB individual_curves=143 B   8.06 KB 
================== ========================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          1.10447   1.79297   3     
make_contexts            0.42552   0.0       792   
get_poes                 0.36848   0.0       744   
total build_hazard_stats 0.06460   1.41797   11    
total split_filter       0.04758   2.04297   1     
combine pmaps            0.04727   1.41797   11    
total read_source_models 0.03957   0.14062   1     
building riskinputs      0.02231   0.00391   1     
saving statistics        0.01637   0.0       11    
managing sources         0.00580   0.0       1     
compute quantile-0.15    0.00389   0.0       11    
compute mean             0.00386   0.0       11    
compute quantile-0.85    0.00341   0.0       11    
store source model       0.00229   0.0       1     
store source_info        0.00178   0.0       1     
aggregate curves         0.00148   0.0       3     
saving probability maps  0.00123   0.0       1     
reading exposure         4.482E-04 0.0       1     
======================== ========= ========= ======