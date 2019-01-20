Virtual Island - City C, 2 SES, grid=0.1
========================================

============== ===================
checksum32     935,710,079        
date           2019-01-20T07:38:54
engine_version 3.4.0-git452d0c6835
============== ===================

num_sites = 281, num_levels = 50

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         2                 
truncation_level                4.0               
rupture_mesh_spacing            10.0              
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.2               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1024              
master_seed                     100               
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,1)    1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================= ========= ========== ==============
grp_id gsims                     distances siteparams ruptparams    
====== ========================= ========= ========== ==============
0      AkkarBommer2010()         rjb       vs30       mag rake      
1      AtkinsonBoore2003SInter() rrup      vs30       hypo_depth mag
====== ========================= ========= ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,AkkarBommer2010(): [0]
  1,AtkinsonBoore2003SInter(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 2,348        2,348       
source_model.xml 1      Subduction Interface 3,345        3,345       
================ ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 5,693
#tot_ruptures 5,693
#tot_weight   5,693
============= =====

Estimated data transfer for the avglosses
-----------------------------------------
548 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 60 tasks = 256.88 KB

Exposure model
--------------
=============== ========
#assets         548     
#taxonomies     11      
deductibile     absolute
insurance_limit absolute
=============== ========

========== ======= ======= === === ========= ==========
taxonomy   mean    stddev  min max num_sites num_assets
MS-FLSB-2  1.25000 0.45227 1   2   12        15        
MS-SLSB-1  1.54545 0.93420 1   4   11        17        
MC-RLSB-2  1.25641 0.88013 1   6   39        49        
W-SLFB-1   1.26506 0.51995 1   3   83        105       
MR-RCSB-2  1.45614 0.79861 1   6   171       249       
MC-RCSB-1  1.28571 0.56061 1   3   21        27        
W-FLFB-2   1.22222 0.50157 1   3   54        66        
PCR-RCSM-5 1.00000 0.0     1   1   2         2         
MR-SLSB-1  1.00000 0.0     1   1   5         5         
A-SPSB-1   1.25000 0.46291 1   2   8         10        
PCR-SLSB-1 1.00000 0.0     1   1   3         3         
*ALL*      0.27803 0.84109 0   10  1,971     548       
========== ======= ======= === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      F         C    0     8     2,348        2.20070   0.0        281       1         2.00000
1      D         C    8     12    3,345        3.59388   0.0        281       1         2.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    5.79457   2     
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ========= ========= ======= =======
operation-duration mean    stddev    min       max     outputs
read_source_models 0.15238 NaN       0.15238   0.15238 1      
split_filter       0.00483 NaN       0.00483   0.00483 1      
sample_ruptures    2.90137 0.98852   2.20238   3.60037 2      
get_eid_rlz        0.00100 2.614E-04 7.343E-04 0.00248 53     
================== ======= ========= ========= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=433 B fnames=118 B            2.17 KB 
split_filter       srcs=1.69 KB srcfilter=253 B dummy=14 B 4.01 KB 
sample_ruptures    param=9.6 KB sources=4.83 KB            47.69 KB
get_eid_rlz        self=89.07 KB                           15.61 KB
================== ======================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total sample_ruptures    5.80275  6.14844   2     
iter_ruptures            5.79038  0.0       2     
total read_source_models 0.15238  0.92969   1     
total get_eid_rlz        0.05301  0.24219   53    
reading exposure         0.04549  0.0       1     
saving ruptures          0.00772  0.0       2     
store source model       0.00578  0.0       1     
total only_filter        0.00483  1.60547   1     
store source_info        0.00215  0.0       1     
======================== ======== ========= ======