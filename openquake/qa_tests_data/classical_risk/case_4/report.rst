Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     3,002,809,595      
date           2019-06-21T09:41:43
engine_version 3.6.0-git17fd0581aa
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

  <RlzsAssoc(size=2, rlzs=2)
  0,'[AkkarBommer2010]': [0]
  0,'[ChiouYoungs2008]': [1]>

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
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
0      231       A    73    77    4,185        0.00236   6.00000   5,685 
0      376       A    128   132   2,220        0.00114   1.00000   2,220 
0      95        A    160   164   1,176        0.0       0.0       0.0   
0      90        A    156   160   285          0.0       0.0       0.0   
0      89        A    152   156   810          0.0       0.0       0.0   
0      8         A    148   152   4,832        0.0       0.0       0.0   
0      68        A    144   148   1,899        0.0       0.0       0.0   
0      45        A    140   144   960          0.0       0.0       0.0   
0      42        A    136   140   1,755        0.0       0.0       0.0   
0      395       A    132   136   2,720        0.0       0.0       0.0   
0      369       A    124   128   826          0.0       0.0       0.0   
0      343       A    120   124   2,926        0.0       0.0       0.0   
0      325       A    116   120   3,934        0.0       0.0       0.0   
0      299       A    112   116   710          0.0       0.0       0.0   
0      298       A    108   112   2,744        0.0       0.0       0.0   
0      291       A    103   108   2,350        0.0       0.0       0.0   
0      288       A    99    103   2,430        0.0       0.0       0.0   
0      28        A    95    99    2,548        0.0       0.0       0.0   
0      270       A    91    95    7,837        0.0       0.0       0.0   
0      27        A    87    91    1,482        0.0       0.0       0.0   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00350   39    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00241 0.00132 0.00140 0.00694 20     
read_source_models 2.32260 NaN     2.32260 2.32260 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== =========================================================== ========
task               sent                                                        received
preclassical       srcs=54.74 KB params=12.01 KB gsims=5.2 KB srcfilter=4.3 KB 5.8 KB  
read_source_models converter=313 B fnames=111 B                                33.88 KB
================== =========================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 2.32260   1.12500   1     
total preclassical       0.04829   1.27734   20    
managing sources         0.01203   0.16406   1     
aggregate curves         0.00347   0.0       20    
store source_info        0.00174   0.0       1     
reading exposure         4.568E-04 0.0       1     
======================== ========= ========= ======