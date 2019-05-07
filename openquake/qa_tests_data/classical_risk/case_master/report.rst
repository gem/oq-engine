classical risk
==============

============== ===================
checksum32     2,021,923,137      
date           2019-05-03T06:43:22
engine_version 3.5.0-git7a6d15e809
============== ===================

num_sites = 7, num_levels = 40, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'classical_risk'  
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
=================================== ================================================================================
Name                                File                                                                            
=================================== ================================================================================
business_interruption_vulnerability `downtime_vulnerability_model.xml <downtime_vulnerability_model.xml>`_          
contents_vulnerability              `contents_vulnerability_model.xml <contents_vulnerability_model.xml>`_          
exposure                            `exposure_model.xml <exposure_model.xml>`_                                      
gsim_logic_tree                     `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                                    
job_ini                             `job.ini <job.ini>`_                                                            
nonstructural_vulnerability         `nonstructural_vulnerability_model.xml <nonstructural_vulnerability_model.xml>`_
occupants_vulnerability             `occupants_vulnerability_model.xml <occupants_vulnerability_model.xml>`_        
source_model_logic_tree             `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                    
structural_vulnerability            `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_      
=================================== ================================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.25000 complex(2,2)    4               
b2        0.75000 complex(2,2)    4               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,'[BooreAtkinson2008]': [0 1]
  0,'[ChiouYoungs2008]': [2 3]
  1,'[AkkarBommer2010]': [0 2]
  1,'[ChiouYoungs2008]': [1 3]
  2,'[BooreAtkinson2008]': [4 5]
  2,'[ChiouYoungs2008]': [6 7]
  3,'[AkkarBommer2010]': [4 6]
  3,'[ChiouYoungs2008]': [5 7]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 482          482         
source_model_1.xml 1      Stable Shallow Crust 4            4           
source_model_2.xml 2      Active Shallow Crust 482          482         
source_model_2.xml 3      Stable Shallow Crust 1            1           
================== ====== ==================== ============ ============

============= ===
#TRT models   4  
#eff_ruptures 969
#tot_ruptures 969
#tot_weight   969
============= ===

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   4         4         
tax2     1.00000 0.0    1   1   2         2         
tax3     1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ========= ==== ===== ===== ============ ========= ========= =======
0      1         S    0     2     482          3.79493   105       1,275  
2      1         S    4     6     482          3.64086   105       1,275  
3      2         X    6     402   1            0.02948   7.00000   2.64575
1      2         S    2     4     4            0.01963   7.00000   10     
====== ========= ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    7.45542   3     
X    0.02948   1     
==== ========= ======

Duplicated sources
------------------
['1']
Found 2 source(s) with the same ID and 1 true duplicate(s)
Here is a fake duplicate: 2

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
read_source_models     0.00751 0.00344 0.00508   0.00994 2      
classical_split_filter 0.13904 0.32602 1.419E-04 0.90758 13     
classical              0.57314 0.20141 0.33806   0.83785 10     
build_hazard_stats     0.01296 0.00361 0.01001   0.01689 7      
====================== ======= ======= ========= ======= =======

Fastest task
------------
taskno=0, weight=482, duration=0 s, sources="2"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   482     NaN    482 482 1
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=482, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   482     NaN    482 482 1
======== ======= ====== === === =

Data transfer
-------------
====================== ============================================================= =========
task                   sent                                                          received 
read_source_models     converter=626 B fnames=236 B                                  13.93 KB 
classical_split_filter srcs=27.31 KB params=12.58 KB gsims=3.45 KB srcfilter=2.77 KB 130.76 KB
classical              srcs=27.31 KB params=12.58 KB gsims=3.45 KB srcfilter=2.77 KB 468.34 KB
build_hazard_stats     pgetter=40.07 KB hstats=1.63 KB N=98 B individual_curves=91 B 16.4 KB  
====================== ============================================================= =========

Slowest operations
------------------
============================ ======== ========= ======
operation                    time_sec memory_mb counts
============================ ======== ========= ======
total classical              5.73139  4.11719   10    
make_contexts                3.06835  0.0       969   
total classical_split_filter 1.80747  2.27344   13    
get_poes                     1.68380  0.0       969   
total build_hazard_stats     0.09074  0.68750   7     
combine pmaps                0.06189  0.68750   7     
building riskinputs          0.03011  0.0       1     
aggregate curves             0.02954  0.08594   13    
compute stats                0.02695  0.0       7     
saving statistics            0.01698  0.0       7     
total read_source_models     0.01502  0.36328   2     
filtering/splitting sources  0.01157  1.77734   3     
saving probability maps      0.00800  0.0       1     
store source model           0.00594  0.07031   2     
managing sources             0.00311  0.0       1     
store source_info            0.00185  0.0       1     
reading exposure             0.00111  0.0       1     
============================ ======== ========= ======