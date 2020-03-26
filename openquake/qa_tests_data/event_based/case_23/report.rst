Example EB Hazard. Infer region from exposure model
===================================================

============== ===================
checksum32     2_006_733_430      
date           2020-03-13T11:21:41
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 93, num_levels = 0, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         5                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.5               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `site_model.csv <site_model.csv>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 2               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================= =========== ======================= =================
grp_id gsims                                   distances   siteparams              ruptparams       
====== ======================================= =========== ======================= =================
0      '[AkkarBommer2010]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================= =========== ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      6.51857   23_314       17_768      
====== ========= ============ ============

Exposure model
--------------
=========== ==
#assets     96
#taxonomies 5 
=========== ==

========================== ======= ======= === === ========= ==========
taxonomy                   mean    stddev  min max num_sites num_assets
Wood                       1.00000 0.0     1   1   23        23        
Adobe                      1.00000 0.0     1   1   29        29        
Stone-Masonry              1.00000 0.0     1   1   16        16        
Unreinforced-Brick-Masonry 1.00000 0.0     1   1   27        27        
Concrete                   1.00000 NaN     1   1   1         1         
*ALL*                      0.03601 0.19229 0   2   2_666     96        
========================== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
235       0      A    3_084        0.06023   8.53632   3_084       
230       0      A    2_436        0.04541   8.74466   2_436       
231       0      A    1_674        0.03831   10        1_674       
227       0      A    820          0.03212   4.43659   820         
236       0      A    3_240        0.02751   1.81944   1_656       
229       0      A    1_050        0.02326   6.45429   1_050       
234       0      A    790          0.02279   11        790         
228       0      A    519          0.02209   4.05202   519         
374       0      A    1_060        0.02198   2.41335   704         
238       0      A    748          0.02122   5.25401   748         
226       0      A    1_088        0.01933   1.75000   552         
232       0      A    620          0.01837   10        620         
376       0      A    888          0.01508   2.30556   540         
240       0      A    480          0.01455   4.38958   480         
239       0      A    480          0.01440   3.95339   472         
279       0      A    70           0.01289   4.93443   61          
233       0      A    294          0.01226   15        294         
386       0      A    273          0.01002   3.74359   273         
243       0      A    1_130        0.00597   0.86809   235         
272       0      A    1_245        0.00594   0.50189   265         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.45491  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.10714 0.04857 0.05137 0.23338 18     
read_source_model  1.00229 NaN     1.00229 1.00229 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            19.45 KB
preclassical      srcs=40.09 KB params=9.23 KB gsims=4.68 KB 6.7 KB  
================= ========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66953                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          1.92859  1.57812   18    
splitting/filtering sources 1.30803  0.58203   18    
composite source model      1.01654  0.0       1     
total read_source_model     1.00229  0.0       1     
reading exposure            0.05500  0.0       1     
aggregate curves            0.00414  0.0       18    
store source_info           0.00220  0.0       1     
=========================== ======== ========= ======