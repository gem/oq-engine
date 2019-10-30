classical risk
==============

============== ===================
checksum32     912,457,779        
date           2019-10-23T16:25:42
engine_version 3.8.0-git2e0d8e6795
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
0      7.00000   482          482         
1      7.00000   4            4.00000     
2      7.00000   482          482         
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
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    482          3.55363   7.00000   482         
1         2      S    482          2.74650   7.00000   482         
2         1      S    4            0.02948   7.00000   4.00000     
2         3      X    1            0.01689   7.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    6.32961  
X    0.01689  
==== =========

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.01118 0.00509 0.00759 0.01478 2      
build_hazard           0.01209 0.00441 0.00877 0.02150 7      
classical              2.43506 0.72226 1.92434 2.94578 2      
classical_split_filter 0.49649 0.40088 0.05042 0.82662 3      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== =========================================== =========
task                   sent                                        received 
SourceReader           apply_unc=2.47 KB ltmodel=378 B fname=230 B 20.25 KB 
classical_split_filter srcs=13.56 KB params=3.14 KB gsims=810 B    73.72 KB 
classical              group=6.56 KB param=2.09 KB gsims=544 B     162.06 KB
build_hazard           pgetter=3.89 KB hstats=1.63 KB N=35 B       16.13 KB 
====================== =========================================== =========

Slowest operations
------------------
============================ ========= ========= ======
calc_44408                   time_sec  memory_mb counts
============================ ========= ========= ======
total classical              4.87013   1.64844   2     
make_contexts                4.25859   0.0       969   
ClassicalCalculator.run      3.24975   0.66406   1     
total classical_split_filter 1.48947   1.35156   3     
computing mean_std           1.34204   0.0       969   
get_poes                     0.36827   0.0       969   
aggregate curves             0.11613   0.03906   5     
total build_hazard           0.08460   0.69922   7     
building riskinputs          0.06829   0.0       1     
saving statistics            0.05896   0.0       7     
read PoEs                    0.04976   0.67969   7     
composite source model       0.03530   0.01953   1     
compute stats                0.03155   0.0       7     
composing pnes               0.02316   0.0       969   
total SourceReader           0.02237   0.45312   2     
saving probability maps      0.02232   0.22266   1     
filtering/splitting sources  0.00338   0.70703   1     
store source_info            0.00220   0.0       1     
combine pmaps                0.00124   0.0       7     
reading exposure             9.592E-04 0.0       1     
============================ ========= ========= ======