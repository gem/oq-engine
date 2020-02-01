classical damage hazard
=======================

============== ===================
checksum32     3_129_914_875      
date           2020-01-16T05:30:56
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 7, num_levels = 79, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
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
=============================== ==================

Input files
-----------
======================= ========================================================================
Name                    File                                                                    
======================= ========================================================================
contents_fragility      `contents_fragility_model.xml <contents_fragility_model.xml>`_          
exposure                `exposure_model.xml <exposure_model.xml>`_                              
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                            
job_ini                 `job_haz.ini <job_haz.ini>`_                                            
nonstructural_fragility `nonstructural_fragility_model.xml <nonstructural_fragility_model.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_            
structural_fragility    `structural_fragility_model.xml <structural_fragility_model.xml>`_      
======================= ========================================================================

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
0      0.21784   482          482         
1      1.75000   4            4.00000     
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
1         0      S    482          0.02703   0.21784   482         
2         1      S    4            0.00298   1.75000   4.00000     
2         3      X    1            0.00209   7.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.03002  
X    0.00209  
==== =========

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.02069 0.00739 0.01547 0.02591 2      
preclassical       0.01715 0.01555 0.00615 0.02815 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.49 KB ltmodel=378 B fname=234 B 18.36 KB
preclassical srcs=12.49 KB params=2.78 KB gsims=538 B    787 B   
============ =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43247                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.04326   0.0       1     
total SourceReader          0.04138   0.36328   2     
total preclassical          0.03430   0.0       2     
store source_info           0.00276   0.0       1     
splitting/filtering sources 7.155E-04 0.0       2     
reading exposure            6.180E-04 0.0       1     
aggregate curves            5.937E-04 0.0       2     
=========================== ========= ========= ======