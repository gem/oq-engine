QA test for disaggregation case_2
=================================

============== ===================
checksum32     131,107,173        
date           2018-06-26T14:58:41
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 2, num_levels = 1

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              1.0              
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            4.0              
complex_fault_mesh_spacing      4.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ======= =============== ================
smlt_path      weight  gsim_logic_tree num_realizations
============== ======= =============== ================
source_model_1 0.50000 simple(2,1)     2/2             
source_model_2 0.50000 simple(2,1)     2/2             
============== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      YoungsEtAl1997SSlab()                 rrup        vs30                    hypo_depth mag   
1      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=4)
  0,YoungsEtAl1997SSlab(): [0 1]
  1,BooreAtkinson2008(): [0]
  1,ChiouYoungs2008(): [1]
  2,BooreAtkinson2008(): [2]
  2,ChiouYoungs2008(): [3]>

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
compute_disagg     1.50381 1.58575 0.42997 5.04204 14       
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== ================================================================================================================================ ========
task           sent                                                                                                                             received
compute_disagg sources=78.51 KB oqparam=28.72 KB cmaker=17.24 KB bin_edges=16.69 KB src_filter=10.91 KB iml4=4.68 KB monitor=4.57 KB trti=196 B 40.79 MB
============== ================================================================================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_disagg           21        10        14    
disaggregate_pne               9.70839   0.0       11,915
disagg_contexts                6.86668   0.0       6,865 
get_closest                    0.66947   0.0       6,865 
build_disagg_matrix            0.08187   1.13672   28    
reading composite source model 0.06934   0.0       1     
splitting sources              0.06218   0.0       1     
unpickling compute_disagg      0.01864   2.83594   14    
reading site collection        2.983E-04 0.0       1     
============================== ========= ========= ======