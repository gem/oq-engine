classical risk
==============

============== ===================
checksum32     4,038,465,672      
date           2019-01-27T08:28:15
engine_version 3.4.0-git7f110aaa0b
============== ===================

num_sites = 7, num_levels = 40

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
b1        0.25000 complex(2,2)    4/4             
b2        0.75000 complex(2,2)    4/4             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): [0 1]
  0,ChiouYoungs2008(): [2 3]
  1,AkkarBommer2010(): [0 2]
  1,ChiouYoungs2008(): [1 3]
  2,BooreAtkinson2008(): [4 5]
  2,ChiouYoungs2008(): [6 7]
  3,AkkarBommer2010(): [4 6]
  3,ChiouYoungs2008(): [5 7]>

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

============= =====
#TRT models   4    
#eff_ruptures 969  
#tot_ruptures 969  
#tot_weight   2,564
============= =====

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
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         S    0     2     482          4.08418   0.00271    105       15        1,275  
2      1         S    4     6     482          3.99535   0.00202    105       15        1,275  
3      2         X    6     402   1            0.02897   5.007E-06  7.00000   1         2.64575
1      2         S    2     4     4            0.02624   8.869E-05  7.00000   1         10     
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    8.10576   3     
X    0.02897   1     
==== ========= ======

Duplicated sources
------------------
['1']
Found 2 source(s) with the same ID and 1 true duplicate(s)
Here is a fake duplicate: 2

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.00789 0.00344 0.00546 0.01032 2      
split_filter       0.04784 NaN     0.04784 0.04784 1      
classical          0.32607 0.07982 0.05574 0.44169 25     
build_hazard_stats 0.01246 0.00289 0.01098 0.01899 7      
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=24, weight=13, duration=0 s, sources="1"

======== ======= ======= ======= === =
variable mean    stddev  min     max n
======== ======= ======= ======= === =
nsites   7.00000 0.0     7       7   2
weight   6.61438 5.61249 2.64575 10  2
======== ======= ======= ======= === =

Slowest task
------------
taskno=12, weight=158, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   7.00000 NaN    7   7   1
weight   158     NaN    158 158 1
======== ======= ====== === === =

Data transfer
-------------
================== =============================================================== =========
task               sent                                                            received 
read_source_models converter=626 B fnames=236 B                                    13.93 KB 
split_filter       srcs=12.22 KB srcfilter=253 B seed=14 B                         18.92 KB 
classical          group=42.13 KB src_filter=27.51 KB param=23.85 KB gsims=5.37 KB 137.75 KB
build_hazard_stats pgetter=36.13 KB hstats=1.68 KB individual_curves=91 B          16.38 KB 
================== =============================================================== =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total classical          8.15183  1.05859   25    
make_contexts            5.02194  0.0       969   
get_poes                 2.76798  0.0       969   
total build_hazard_stats 0.08721  1.48047   7     
combine pmaps            0.05352  1.40625   7     
total split_filter       0.04784  2.06250   1     
building riskinputs      0.02998  0.03906   1     
saving statistics        0.02132  0.0       7     
total read_source_models 0.01578  0.20703   2     
aggregate curves         0.00867  0.0       25    
managing sources         0.00862  0.05078   1     
compute quantile-0.15    0.00832  0.0       7     
compute quantile-0.5     0.00822  0.0       7     
compute quantile-0.85    0.00820  0.0       7     
compute mean             0.00677  0.08594   7     
saving probability maps  0.00440  0.0       1     
store source model       0.00437  0.0       2     
store source_info        0.00182  0.0       1     
reading exposure         0.00139  0.05859   1     
======================== ======== ========= ======