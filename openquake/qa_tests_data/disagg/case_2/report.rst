QA test for disaggregation case_2
=================================

============== ===================
checksum32     131,107,173        
date           2018-09-05T10:03:44
engine_version 3.2.0-gitb4ef3a4b6c
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
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.03432 0.03004 0.01308 0.05557 2        
compute_disagg       1.35732 1.51281 0.41964 4.77020 14       
==================== ======= ======= ======= ======= =========

Data transfer
-------------
==================== =============================================================================================================================== ========
task                 sent                                                                                                                            received
pickle_source_models monitor=618 B converter=578 B fnames=360 B                                                                                      312 B   
compute_disagg       sources=80.08 KB oqparam=28.72 KB cmaker=18.21 KB bin_edges=16.69 KB src_filter=9.83 KB iml4=4.68 KB monitor=4.27 KB trti=196 B 40.79 MB
==================== =============================================================================================================================== ========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
total compute_disagg       19       11        14    
disaggregate_pne           8.75335  0.0       11,915
disagg_contexts            6.14352  0.0       6,865 
get_closest                0.63597  0.0       6,865 
build_disagg_matrix        0.07032  3.56641   28    
total pickle_source_models 0.06865  4.44531   2     
splitting sources          0.06441  0.0       1     
========================== ======== ========= ======