Virtual Island - City C, 2 SES, grid=0.1
========================================

============== ===================
checksum32     3,478,425,557      
date           2019-02-18T08:36:58
engine_version 3.4.0-git9883ae17a5
============== ===================

num_sites = 281, num_levels = 50

Parameters
----------
=============================== ==================
calculation_mode                'ebrisk'          
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
b1        1.00000 trivial(1,1)    1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =========================== ========= ========== ==============
grp_id gsims                       distances siteparams ruptparams    
====== =========================== ========= ========== ==============
0      '[AkkarBommer2010]'         rjb       vs30       mag rake      
1      '[AtkinsonBoore2003SInter]' rrup      vs30       hypo_depth mag
====== =========================== ========= ========== ==============

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,'[AkkarBommer2010]': [0]
  1,'[AtkinsonBoore2003SInter]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 2,348        2,348       
source_model.xml 1      Subduction Interface 3,345        3,345       
================ ====== ==================== ============ ============

============= ======
#TRT models   2     
#eff_ruptures 5,693 
#tot_ruptures 5,693 
#tot_weight   22,772
============= ======

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
*ALL*      1.95018 1.30562 1   10  281       548       
========== ======= ======= === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
1      D         C    8     12    3,345        3.84226   0.0        1.00000   0         2.00000
0      F         C    0     8     2,348        2.35751   0.0        1.00000   0         2.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    6.19976   2     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ======= =======
operation-duration mean      stddev    min       max     outputs
read_source_models 0.16426   NaN       0.16426   0.16426 1      
sample_ruptures    3.11094   1.05864   2.36237   3.85951 2      
get_eid_rlz        8.684E-04 1.140E-04 6.757E-04 0.00111 30     
================== ========= ========= ========= ======= =======

Data transfer
-------------
================== ============================================= ========
task               sent                                          received
read_source_models converter=358 B fnames=118 B                  2.23 KB 
sample_ruptures    param=9.49 KB sources=2.38 KB srcfilter=440 B 44.83 KB
get_eid_rlz        self=56.86 KB                                 9.74 KB 
================== ============================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total sample_ruptures    6.22188  7.39062   2     
iter_ruptures            6.19524  0.0       2     
total read_source_models 0.16426  1.00000   1     
reading exposure         0.04247  0.0       1     
total get_eid_rlz        0.02605  0.20312   30    
saving ruptures          0.01018  0.0       2     
store source model       0.00957  0.0       1     
store source_info        0.00222  0.0       1     
======================== ======== ========= ======