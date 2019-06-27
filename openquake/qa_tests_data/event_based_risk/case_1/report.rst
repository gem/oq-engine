Event Based Risk QA Test 1
==========================

============== ===================
checksum32     982,890,157        
date           2019-06-24T15:34:01
engine_version 3.6.0-git4b6205639c
============== ===================

num_sites = 3, num_levels = 25, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         20                
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
=========================== ====================================================================
Name                        File                                                                
=========================== ====================================================================
exposure                    `exposure1.xml <exposure1.xml>`_                                    
gsim_logic_tree             `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                        
job_ini                     `job.ini <job.ini>`_                                                
nonstructural_vulnerability `vulnerability_model_nonstco.xml <vulnerability_model_nonstco.xml>`_
source_model_logic_tree     `source_model_logic_tree.xml <source_model_logic_tree.xml>`_        
structural_vulnerability    `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_      
=========================== ====================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================= =========== ======================= =================
grp_id gsims                                   distances   siteparams              ruptparams       
====== ======================================= =========== ======================= =================
0      '[AkkarBommer2010]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 18           18          
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 2 realization(s) x 2 loss type(s) losses x 8 bytes x 20 tasks = 2.5 KB

Exposure model
--------------
=========== =
#assets     4
#taxonomies 3
=========== =

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
RM       1.00000 0.0     1   1   2         2         
RC       1.00000 NaN     1   1   1         1         
W        1.00000 NaN     1   1   1         1         
*ALL*    1.33333 0.57735 1   2   3         4         
======== ======= ======= === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight  checksum     
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
0      1         P    0     1     6            0.00301   0.0       4.00000 925,913,543  
0      2         P    1     2     6            0.00294   0.0       2.00000 1,979,470,468
0      3         P    2     3     6            0.00195   0.0       8.00000 2,157,728,551
====== ========= ==== ===== ===== ============ ========= ========= ======= =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00790   3     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ======= =======
operation-duration mean      stddev    min       max     outputs
get_eid_rlz        6.654E-04 2.587E-04 3.047E-04 0.00115 8      
read_source_models 0.00282   NaN       0.00282   0.00282 1      
sample_ruptures    0.01256   NaN       0.01256   0.01256 1      
================== ========= ========= ========= ======= =======

Data transfer
-------------
================== ============================================= ========
task               sent                                          received
get_eid_rlz        self=12.67 KB                                 2.34 KB 
read_source_models converter=313 B fnames=113 B                  2.28 KB 
sample_ruptures    param=4.01 KB sources=1.94 KB srcfilter=220 B 1.94 KB 
================== ============================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total sample_ruptures    0.01256  0.0       1     
total get_eid_rlz        0.00532  0.0       8     
total read_source_models 0.00282  0.0       1     
saving ruptures          0.00219  0.0       1     
store source model       0.00164  0.0       1     
store source_info        0.00159  0.0       1     
reading exposure         0.00138  0.0       1     
======================== ======== ========= ======