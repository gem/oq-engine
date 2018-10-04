classical risk
==============

============== ===================
checksum32     2,559,514,760      
date           2018-10-03T15:00:19
engine_version 3.3.0-gitd9f5dca908
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
source                              `source_model_1.xml <source_model_1.xml>`_                                      
source                              `source_model_2.xml <source_model_2.xml>`_                                      
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
0      1         S    0     2     482          6.50245   0.00486    105       15        1,275  
1      2         S    2     4     4            0.02622   1.574E-05  7.00000   1         10     
2      1         S    0     2     482          6.83926   0.00379    105       15        1,275  
3      2         X    2     398   1            0.02717   5.484E-06  7.00000   1         2.64575
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    13        3     
X    0.02717   1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.01575 0.00844   0.00978 0.02172 2      
split_filter       0.08131 NaN       0.08131 0.08131 1      
classical          1.03605 0.42583   0.05703 1.50988 13     
build_hazard_stats 0.01880 7.518E-04 0.01786 0.02021 7      
================== ======= ========= ======= ======= =======

Fastest task
------------
taskno=13, weight=13, duration=0 s, sources="2"

======== ======= ======= ======= === =
variable mean    stddev  min     max n
======== ======= ======= ======= === =
nsites   7.00000 0.0     7       7   2
weight   6.61438 5.61249 2.64575 10  2
======== ======= ======= ======= === =

Slowest task
------------
taskno=11, weight=264, duration=1 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   7.00000 0.0    7   7   3
weight   88      16     74  105 3
======== ======= ====== === === =

Data transfer
-------------
================== ============================================================================= ========
task               sent                                                                          received
read_source_models monitor=736 B converter=638 B fnames=386 B                                    13.85 KB
split_filter       srcs=12.14 KB monitor=381 B srcfilter=253 B sample_factor=21 B seed=14 B      18.73 KB
classical          group=29.7 KB param=12.94 KB monitor=4.38 KB src_filter=2.79 KB gsims=2.79 KB 73.82 KB
build_hazard_stats pgetter=32.53 KB monitor=2.42 KB hstats=1.68 KB                               16.38 KB
================== ============================================================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total classical          13       2.39844   13    
make_contexts            8.07051  0.0       969   
get_poes                 4.70557  0.0       969   
updating source_info     0.85345  0.0       1     
iter_ruptures            0.58480  0.0       32    
total build_hazard_stats 0.13161  1.57422   7     
total split_filter       0.08131  1.06250   1     
combine pmaps            0.07678  1.53906   7     
building riskinputs      0.05896  0.0       1     
store source_info        0.03950  0.78125   13    
total read_source_models 0.03150  0.44141   2     
saving statistics        0.02755  0.0       7     
managing sources         0.02597  0.0       1     
compute quantile-0.5     0.01096  0.0       7     
compute quantile-0.15    0.01092  0.14062   7     
compute quantile-0.85    0.01068  0.0       7     
saving probability maps  0.00714  0.0       1     
aggregate curves         0.00457  0.0       13    
compute mean             0.00362  0.0       7     
reading exposure         0.00214  0.06250   1     
======================== ======== ========= ======