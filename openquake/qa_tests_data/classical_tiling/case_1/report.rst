Classical PSHA using Area Source
================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_80600.hdf5 Thu Jan 26 05:26:42 2017
engine_version                                 2.3.0-gitd31dc69        
hazardlib_version                              0.23.0-git4d14bee       
============================================== ========================

num_sites = 6, sitecol = 992 B

Parameters
----------
=============================== ===============================
calculation_mode                'classical'                    
number_of_logic_tree_samples    0                              
maximum_distance                {'Active Shallow Crust': 200.0}
investigation_time              50.0                           
ses_per_logic_tree_path         1                              
truncation_level                3.0                            
rupture_mesh_spacing            2.0                            
complex_fault_mesh_spacing      2.0                            
width_of_mfd_bin                0.2                            
area_source_discretization      5.0                            
ground_motion_correlation_model None                           
random_seed                     23                             
master_seed                     0                              
sites_per_tile                  1                              
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
b1        1.000  `source_model.xml <source_model.xml>`_ simple(2)       2/2             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rrup rx rjb z1pt0 vs30 vs30measured dip rake mag ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,BooreAtkinson2008(): ['<0,b1~b1,w=0.6>']
  0,ChiouYoungs2008(): ['<1,b1~b2,w=0.4>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           1640         1,640       
================ ====== ==================== =========== ============ ============

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,800       
count_eff_ruptures_num_tasks                1           
count_eff_ruptures_sent.gsims               179         
count_eff_ruptures_sent.monitor             1,577       
count_eff_ruptures_sent.sitecol             698         
count_eff_ruptures_sent.sources             1,918       
count_eff_ruptures_tot_received             1,800       
hazard.input_weight                         164         
hazard.n_imts                               3           
hazard.n_levels                             57          
hazard.n_realizations                       2           
hazard.n_sites                              6           
hazard.n_sources                            1           
hazard.output_weight                        684         
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         AreaSource   1,640        0.0       6         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       1     
============ ========= ======

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
count_eff_ruptures 9.665E-04 NaN    9.665E-04 9.665E-04 1        
================== ========= ====== ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.080     0.0       1     
reading site collection          0.003     0.0       1     
managing sources                 0.002     0.0       1     
filtering composite source model 0.001     0.0       1     
total count_eff_ruptures         9.665E-04 0.0       1     
store source_info                7.517E-04 0.0       1     
saving probability maps          3.505E-05 0.0       1     
aggregate curves                 2.289E-05 0.0       1     
================================ ========= ========= ======