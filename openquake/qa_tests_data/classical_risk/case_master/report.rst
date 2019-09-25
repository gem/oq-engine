classical risk
==============

============== ===================
checksum32     2,856,913,760      
date           2019-09-24T15:20:49
engine_version 3.7.0-git749bb363b3
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
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
1         0      S    482          2.12662   3,374     482          226  
2         1      S    4            0.02913   35        5.00000      171  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    2.15574   3     
X    0.0       1     
==== ========= ======

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
build_hazard           0.01608 0.00321 0.01162 0.01867 7      
classical_split_filter 0.54189 0.89872 0.01584 1.87922 4      
read_source_models     0.01135 0.00107 0.01060 0.01211 2      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ============================================== =========
task                   sent                                           received 
build_hazard           pgetter=3.88 KB hstats=1.63 KB N=35 B          16.13 KB 
classical_split_filter srcs=12.49 KB params=2.01 KB srcfilter=1.84 KB 229.54 KB
read_source_models     converter=628 B fnames=236 B                   13.94 KB 
====================== ============================================== =========

Slowest operations
------------------
============================ ========= ========= ======
calc_1704                    time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      2.33699   2.50391   1     
total classical_split_filter 2.16755   1.33594   4     
make_contexts                1.37528   0.0       487   
computing mean_std           0.47010   0.0       487   
get_poes                     0.17546   0.0       487   
total build_hazard           0.11254   1.76953   7     
read PoEs                    0.08732   1.76953   7     
aggregate curves             0.06231   1.03125   4     
building riskinputs          0.04052   0.0       1     
total read_source_models     0.02270   0.21484   2     
compute stats                0.02102   0.0       7     
saving statistics            0.01789   0.0       7     
filtering/splitting sources  0.00674   0.36328   2     
saving probability maps      0.00639   0.0       1     
store source_info            0.00232   0.0       1     
combine pmaps                0.00138   0.0       7     
reading exposure             7.291E-04 0.0       1     
managing sources             3.374E-04 0.0       1     
============================ ========= ========= ======