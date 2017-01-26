Event Based from NonParametric source
=====================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_80579.hdf5 Thu Jan 26 05:25:58 2017
engine_version                                 2.3.0-gitd31dc69        
hazardlib_version                              0.23.0-git4d14bee       
============================================== ========================

num_sites = 3, sitecol = 854 B

Parameters
----------
=============================== ===============================
calculation_mode                'event_based_rupture'          
number_of_logic_tree_samples    0                              
maximum_distance                {'Active Shallow Crust': 500.0}
investigation_time              50.0                           
ses_per_logic_tree_path         1                              
truncation_level                3.0                            
rupture_mesh_spacing            5.0                            
complex_fault_mesh_spacing      5.0                            
width_of_mfd_bin                0.3                            
area_source_discretization      10.0                           
ground_motion_correlation_model None                           
random_seed                     23                             
master_seed                     0                              
=============================== ===============================

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
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rrup rx rjb z1pt0 vs30 vs30measured dip rake mag ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1~b1,w=1.0>']>

Informational data
------------------
====================== ============
hazard.input_weight    4.000       
hazard.n_imts          1           
hazard.n_levels        7           
hazard.n_realizations  1           
hazard.n_sites         3           
hazard.n_sources       1           
hazard.output_weight   21          
hostname               gem-tstation
require_epsilons       False       
====================== ============

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.079     0.0       1     
filtering composite source model 0.002     0.0       1     
reading site collection          3.242E-05 0.0       1     
================================ ========= ========= ======