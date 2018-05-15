Event Based from NonParametric source
=====================================

============== ===================
checksum32     103,533,850        
date           2018-05-15T04:14:07
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 3, num_levels = 7

Parameters
----------
=============================== =====================
calculation_mode                'event_based_rupture'
number_of_logic_tree_samples    0                    
maximum_distance                {'default': 500.0}   
investigation_time              50.0                 
ses_per_logic_tree_path         2                    
truncation_level                3.0                  
rupture_mesh_spacing            5.0                  
complex_fault_mesh_spacing      5.0                  
width_of_mfd_bin                0.3                  
area_source_discretization      20.0                 
ground_motion_correlation_model None                 
minimum_intensity               {}                   
random_seed                     23                   
master_seed                     0                    
ses_seed                        42                   
=============================== =====================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.06844   0.0       1     
splitting sources              3.533E-04 0.0       1     
reading site collection        9.918E-05 0.0       1     
============================== ========= ========= ======