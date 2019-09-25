Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     3,002,809,595      
date           2019-09-24T15:20:46
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 6, num_levels = 19, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job_haz.ini <job_haz.ini>`_                                
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================= =========== ======================= =================
grp_id gsims                                   distances   siteparams              ruptparams       
====== ======================================= =========== ======================= =================
0      '[AkkarBommer2010]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 6,405        91,021      
================ ====== ==================== ============ ============

Exposure model
--------------
=========== =
#assets     6
#taxonomies 2
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
W        1.00000 0.0    1   1   5         5         
A        1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   6         6         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ==========
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed     
========= ====== ==== ============ ========= ========= ============ ==========
231       0      A    4,185        2.313E-04 6.00000   4,185        18,096,044
376       0      A    2,220        1.798E-04 1.00000   2,220        12,349,277
========= ====== ==== ============ ========= ========= ============ ==========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    4.110E-04 39    
==== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ======= =======
operation-duration mean      stddev    min       max     outputs
preclassical       5.994E-04 1.830E-04 3.235E-04 0.00102 20     
read_source_models 2.05413   NaN       2.05413   2.05413 1      
================== ========= ========= ========= ======= =======

Data transfer
-------------
================== ================================================ ========
task               sent                                             received
preclassical       srcs=55.34 KB srcfilter=17.56 KB params=12.77 KB 5.8 KB  
read_source_models converter=314 B fnames=111 B                     33.99 KB
================== ================================================ ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1703                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 2.05413   0.84375   1     
total preclassical       0.01199   0.18750   20    
aggregate curves         0.00499   0.0       20    
store source_info        0.00195   0.0       1     
managing sources         7.184E-04 0.0       1     
reading exposure         4.368E-04 0.0       1     
======================== ========= ========= ======