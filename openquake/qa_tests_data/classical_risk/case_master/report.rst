classical risk
==============

============== ===================
checksum32     2,856,913,760      
date           2019-06-24T15:33:15
engine_version 3.6.0-git4b6205639c
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
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight  checksum     
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
0      1         S    0     2     482          3.70562   7.00000   669     1,858,878,648
3      2         X    6     402   1            0.03307   7.00000   1.38918 953,932,561  
1      2         S    2     4     4            0.01929   7.00000   5.55673 2,443,917,473
2      1         S    4     6     482          0.0       0.0       0.0     1,858,878,648
====== ========= ==== ===== ===== ============ ========= ========= ======= =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    3.72491   3     
X    0.03307   1     
==== ========= ======

Duplicated sources
------------------
Found 2 source(s) with the same ID and 1 true duplicate(s): ['1']
Here is a fake duplicate: 2

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
build_hazard_stats     0.01579 0.00281 0.01102   0.01808 7      
classical              0.40333 0.12375 0.31119   0.69547 9      
classical_split_filter 0.01637 0.03572 1.559E-04 0.10967 11     
read_source_models     0.01467 0.00252 0.01289   0.01646 2      
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
taskno=0, weight=482, duration=0 s, sources="2"

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
build_hazard_stats     pgetter=3.18 KB hstats=1.63 KB N=98 B individual_curves=91 B  16.13 KB 
classical              srcs=25.11 KB params=10.65 KB gsims=2.92 KB srcfilter=2.36 KB 532.04 KB
classical_split_filter srcs=25.11 KB params=10.65 KB gsims=2.92 KB srcfilter=2.36 KB 57.28 KB 
read_source_models     converter=626 B fnames=236 B                                  13.94 KB 
====================== ============================================================= =========

Slowest operations
------------------
============================ ======== ========= ======
operation                    time_sec memory_mb counts
============================ ======== ========= ======
total classical              3.62996  2.22656   9     
make_contexts                1.56886  0.0       487   
get_poes                     0.87382  0.0       487   
total classical_split_filter 0.18010  1.47656   11    
total build_hazard_stats     0.11052  0.17188   7     
read PoEs                    0.07798  0.17188   7     
aggregate curves             0.03588  0.25781   11    
building riskinputs          0.03245  0.0       1     
total read_source_models     0.02934  0.23828   2     
compute stats                0.02674  0.0       7     
saving statistics            0.01641  0.0       7     
filtering/splitting sources  0.01434  0.78125   2     
saving probability maps      0.01289  0.0       1     
store source model           0.00631  0.0       2     
managing sources             0.00282  0.0       1     
combine pmaps                0.00246  0.0       7     
store source_info            0.00219  0.0       1     
reading exposure             0.00101  0.0       1     
============================ ======== ========= ======