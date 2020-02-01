classical risk
==============

============== ===================
checksum32     912_457_779        
date           2020-01-16T05:30:33
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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
2      NaN       482          0.0         
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
1         0      S    482          1.99524   7.00000   482         
2         3      X    1            0.01758   7.00000   1.00000     
2         1      S    4            0.01259   7.00000   4.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    2.00783  
X    0.01758  
==== =========

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.01477 0.01066 0.00723 0.02231 2      
build_hazard           0.01557 0.00227 0.01103 0.01798 7      
classical_split_filter 1.03296 1.40682 0.03819 2.02774 2      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== =========================================== =========
task                   sent                                        received 
SourceReader           apply_unc=2.47 KB ltmodel=378 B fname=230 B 18.35 KB 
classical_split_filter srcs=12.49 KB params=2.29 KB gsims=538 B    214.62 KB
build_hazard           pgetter=3.89 KB hstats=1.63 KB N=35 B       15.63 KB 
====================== =========================================== =========

Slowest operations
------------------
============================ ========= ========= ======
calc_43190                   time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      2.25316   1.38672   1     
total classical_split_filter 2.06593   1.35156   2     
make_contexts                1.34166   0.0       17    
computing mean_std           0.42781   0.0       487   
get_poes                     0.11838   0.0       487   
total build_hazard           0.10901   2.06250   7     
read PoEs                    0.08201   2.06250   7     
iter_ruptures                0.07048   0.0       17    
aggregate curves             0.04302   0.94531   2     
building riskinputs          0.04196   0.0       1     
composite source model       0.03705   0.0       1     
splitting/filtering sources  0.03587   0.66016   2     
total SourceReader           0.02955   0.0       2     
composing pnes               0.02327   0.0       487   
compute stats                0.02125   0.0       7     
saving statistics            0.01414   0.0       7     
saving probability maps      0.00680   0.0       1     
store source_info            0.00233   0.0       1     
combine pmaps                0.00152   0.0       7     
reading exposure             7.253E-04 0.0       1     
============================ ========= ========= ======