classical risk
==============

============== ===================
checksum32     2,856,913,760      
date           2019-07-30T15:04:01
engine_version 3.7.0-git3b3dff46da
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

  <RlzsAssoc(size=16, rlzs=8)>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 482          482         
source_model_1.xml 1      Stable Shallow Crust 5            4           
source_model_2.xml 2      Active Shallow Crust 482          482         
source_model_2.xml 3      Stable Shallow Crust 5            1           
================== ====== ==================== ============ ============

============= ===
#TRT models   4  
#eff_ruptures 974
#tot_ruptures 969
============= ===

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   4         4         
tax2     1.00000 0.0    1   1   2         2         
tax3     1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ======= =====
source_id grp_id code num_ruptures calc_time num_sites weight  speed
========= ====== ==== ============ ========= ========= ======= =====
1         0      S    482          4.93662   3,374     482     97   
2         1      S    4            0.06623   35        5.00000 75   
========= ====== ==== ============ ========= ========= ======= =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    5.00286   3     
X    0.0       1     
==== ========= ======

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
build_hazard           0.02512 0.00741 0.01478 0.03454 7      
classical_split_filter 1.67334 1.70514 0.07088 3.46532 3      
read_source_models     0.00855 0.00399 0.00573 0.01137 2      
====================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=1, weight=5, duration=0 s, sources="2"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   7.00000 NaN    7.00000 7.00000 1
weight   5.00000 NaN    5.00000 5.00000 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=0, weight=482, duration=3 s, sources="1"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   7.00000 NaN    7.00000 7.00000 1
weight   482     NaN    482     482     1
======== ======= ====== ======= ======= =

Data transfer
-------------
====================== ================================================================================== =========
task                   sent                                                                               received 
build_hazard           pgetter=3.18 KB hstats=1.63 KB max_sites_disagg=35 B N=35 B individual_curves=28 B 16.13 KB 
classical_split_filter srcs=12.47 KB params=2.01 KB gsims=538 B srcfilter=440 B                           233.08 KB
read_source_models     converter=628 B fnames=222 B                                                       13.93 KB 
====================== ================================================================================== =========

Slowest operations
------------------
============================ ========= ========= ======
calc_15511                   time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      5.23365   1.54297   1     
total classical_split_filter 5.02002   0.16016   3     
make_contexts                2.02841   0.0       487   
get_poes                     1.20876   0.0       487   
total build_hazard           0.17583   1.28516   7     
read PoEs                    0.09455   1.28516   7     
aggregate curves             0.07713   0.51172   3     
compute stats                0.07634   0.0       7     
building riskinputs          0.03068   0.0       1     
total read_source_models     0.01710   0.0       2     
saving statistics            0.01643   0.0       7     
filtering/splitting sources  0.00865   0.0       2     
saving probability maps      0.00737   0.0       1     
store source_info            0.00287   0.0       1     
combine pmaps                0.00188   0.0       7     
managing sources             0.00132   0.0       1     
reading exposure             6.089E-04 0.0       1     
============================ ========= ========= ======