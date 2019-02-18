classical risk
==============

============== ===================
checksum32     2,021,923,137      
date           2019-02-18T08:35:20
engine_version 3.4.0-git9883ae17a5
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
0      1         S    0     2     482          3.96014   0.00269    105       15        1,275  
2      1         S    4     6     482          3.51837   0.00316    105       15        1,275  
3      2         X    6     402   1            0.02781   4.292E-06  7.00000   1         2.64575
1      2         S    2     4     4            0.01873   1.860E-05  7.00000   1         10     
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    7.49723   3     
X    0.02781   1     
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
read_source_models 0.00785 0.00367 0.00525 0.01044 2      
split_filter       0.02353 0.02686 0.00453 0.04252 2      
classical          0.30312 0.08107 0.04817 0.46783 25     
build_hazard_stats 0.01206 0.00195 0.01082 0.01579 7      
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
taskno=2, weight=132, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   7.00000 NaN    7   7   1
weight   132     NaN    132 132 1
======== ======= ====== === === =

Data transfer
-------------
================== ============================================================== =========
task               sent                                                           received 
read_source_models converter=626 B fnames=236 B                                   13.93 KB 
split_filter       srcs=11.32 KB srcfilter=253 B seed=14 B                        19.47 KB 
classical          group=42.13 KB param=23.85 KB gsims=6.63 KB src_filter=5.37 KB 641.92 KB
build_hazard_stats pgetter=35.63 KB hstats=1.68 KB N=98 B individual_curves=91 B  16.88 KB 
================== ============================================================== =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total classical          7.57804  2.51953   25    
make_contexts            3.09113  0.0       969   
get_poes                 1.75821  0.0       969   
total build_hazard_stats 0.08444  0.70312   7     
combine pmaps            0.04818  0.70312   7     
aggregate curves         0.04716  0.96094   25    
total split_filter       0.04705  1.93359   2     
building riskinputs      0.03052  0.03906   1     
saving statistics        0.02227  0.0       7     
total read_source_models 0.01570  0.17188   2     
saving probability maps  0.01223  0.82812   1     
compute quantile-0.85    0.00906  0.0       7     
compute quantile-0.5     0.00890  0.0       7     
store source model       0.00885  0.03125   2     
compute quantile-0.15    0.00856  0.0       7     
managing sources         0.00833  0.0       1     
compute mean             0.00653  0.0       7     
store source_info        0.00210  0.0       1     
reading exposure         0.00158  0.01953   1     
======================== ======== ========= ======