disaggregation with a complex logic tree
========================================

============== ===================
checksum32     2,607,118,707      
date           2019-10-02T10:07:13
engine_version 3.8.0-git6f03622c6e
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
0      2.00000   543          543         
1      2.00000   4            4.00000     
2      2.00000   543          543         
3      2.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         2      S    543          0.00617   0.00368   543         
2         1      S    4            0.00578   0.50000   4.00000     
1         0      S    543          0.00491   0.00368   543         
2         3      X    1            2.201E-04 2.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.01686   3     
X    2.201E-04 1     
==== ========= ======

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.02127 0.00687   0.01640 0.02613 2      
preclassical       0.00622 7.499E-04 0.00536 0.00673 3      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.41 KB ltmodel=378 B fname=214 B 20.35 KB
preclassical srcs=13.56 KB params=4.08 KB gsims=810 B    1.05 KB 
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_29434             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.04254  0.0       1     
total SourceReader     0.04253  0.0       2     
total preclassical     0.01867  0.51562   3     
store source_info      0.00258  0.0       1     
aggregate curves       0.00102  0.0       3     
====================== ======== ========= ======