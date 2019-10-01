classical risk
==============

============== ===================
checksum32     2,856,913,760      
date           2019-10-01T06:32:12
engine_version 3.8.0-git66affb82eb
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3,374     482          482         
1      28        4            4.00000     
2      3,374     482          482         
3      7.00000   1            1.00000     
====== ========= ============ ============

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
1         0      S    482          2.16642   3,374     482          222  
1         2      S    482          2.14123   3,374     482          225  
2         1      S    4            0.01782   28        4.00000      224  
2         3      X    1            0.01595   7.00000   1.00000      62   
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    4.32546   3     
X    0.01595   1     
==== ========= ======

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.01528 0.00270 0.01337 0.01718 2      
build_hazard           0.01626 0.00263 0.01141 0.01824 7      
classical_split_filter 0.72744 0.93747 0.01633 1.94173 6      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== =========================================== =========
task                   sent                                        received 
SourceReader           apply_unc=2.47 KB ltmodel=378 B fname=230 B 17.24 KB 
build_hazard           pgetter=3.88 KB hstats=1.63 KB N=35 B       16.13 KB 
classical_split_filter srcs=13.56 KB params=3.02 KB gsims=810 B    236.87 KB
====================== =========================================== =========

Slowest operations
------------------
============================ ========= ========= ======
calc_6357                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical_split_filter 4.36466   1.74219   6     
make_contexts                2.76876   0.0       969   
ClassicalCalculator.run      2.35263   1.27734   1     
computing mean_std           0.95265   0.0       969   
get_poes                     0.35336   0.0       969   
total build_hazard           0.11380   0.80469   7     
read PoEs                    0.08841   0.79297   7     
aggregate curves             0.07537   1.03125   6     
building riskinputs          0.03246   0.13672   1     
composite source model       0.03063   0.0       1     
total SourceReader           0.03056   0.42578   2     
compute stats                0.02114   0.0       7     
filtering/splitting sources  0.01598   0.92188   3     
saving statistics            0.01423   0.0       7     
saving probability maps      0.00691   0.0       1     
store source_info            0.00233   0.0       1     
combine pmaps                0.00139   0.0       7     
reading exposure             7.796E-04 0.0       1     
============================ ========= ========= ======