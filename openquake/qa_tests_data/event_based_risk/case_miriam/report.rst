Virtual Island - City C, 2 SES, grid=0.1
========================================

============== ===================
checksum32     4,129,458,072      
date           2019-10-01T07:01:01
engine_version 3.8.0-gitbd71c2f960
============== ===================

num_sites = 281, num_levels = 50, num_rlzs = 1

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

  <RlzsAssoc(size=2, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      281       2,348        2.00000     
1      281       3,345        2.00000     
====== ========= ============ ============

Exposure model
--------------
=========== ===
#assets     548
#taxonomies 11 
=========== ===

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
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
D         1      C    3,345        3.81940   281       2.00000      0.52364
F         0      C    2,348        2.34640   281       2.00000      0.85237
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    6.16580   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.19787 NaN     0.19787 0.19787 1      
sample_ruptures    3.10067 1.05358 2.35567 3.84566 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
=============== ============================================ ========
task            sent                                         received
SourceReader                                                 4.18 KB 
sample_ruptures param=9.4 KB sources=2.39 KB srcfilter=444 B 45.82 KB
=============== ============================================ ========

Slowest operations
------------------
======================== ======== ========= ======
calc_6611                time_sec memory_mb counts
======================== ======== ========= ======
total sample_ruptures    6.20133  2.78516   2     
EventBasedCalculator.run 4.48683  2.73828   1     
composite source model   0.20699  0.25391   1     
total SourceReader       0.19787  0.25391   1     
reading exposure         0.04460  0.0       1     
saving events            0.02570  0.25781   1     
saving ruptures          0.00865  0.0       2     
store source_info        0.00279  0.77344   1     
======================== ======== ========= ======