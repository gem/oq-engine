disaggregation with a complex logic tree
========================================

============== ===================
checksum32     217_019_414        
date           2020-01-16T05:30:44
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 2, num_levels = 102, num_rlzs = 8

Parameters
----------
=============================== =================
calculation_mode                'preclassical'   
number_of_logic_tree_samples    0                
maximum_distance                {'default': 60.0}
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
=============================== =================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

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
0      0.05525   543          543         
1      0.50000   4            4.00000     
2      NaN       543          0.0         
3      2.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    543          0.03357   0.05525   543         
2         1      S    4            0.00201   0.50000   4.00000     
2         3      X    1            0.00166   2.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.03558  
X    0.00166  
==== =========

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.02004 0.00634 0.01556 0.02453 2      
preclassical       0.01985 0.02173 0.00449 0.03521 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.41 KB ltmodel=378 B fname=214 B 18.38 KB
preclassical srcs=12.49 KB params=3 KB gsims=538 B       787 B   
============ =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43226                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.04036   0.0       1     
total SourceReader          0.04008   0.0       2     
total preclassical          0.03970   0.54297   2     
store source_info           0.00245   0.0       1     
splitting/filtering sources 9.809E-04 0.0       2     
aggregate curves            4.444E-04 0.0       2     
=========================== ========= ========= ======