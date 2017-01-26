Classical PSHA - Loss fractions QA test
=======================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_80502.hdf5 Thu Jan 26 05:24:13 2017
engine_version                                 2.3.0-gitd31dc69        
hazardlib_version                              0.23.0-git4d14bee       
============================================== ========================

num_sites = 13, sitecol = 1.28 KB

Parameters
----------
=============================== ===============================
calculation_mode                'classical_risk'               
number_of_logic_tree_samples    1                              
maximum_distance                {'Active Shallow Crust': 200.0}
investigation_time              50.0                           
ses_per_logic_tree_path         1                              
truncation_level                3.0                            
rupture_mesh_spacing            5.0                            
complex_fault_mesh_spacing      5.0                            
width_of_mfd_bin                0.2                            
area_source_discretization      10.0                           
ground_motion_correlation_model None                           
random_seed                     23                             
master_seed                     0                              
avg_losses                      False                          
sites_per_tile                  10000                          
=============================== ===============================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

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

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 2           2132         2,132       
================ ====== ==================== =========== ============ ============

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,322       
count_eff_ruptures_num_tasks                2           
count_eff_ruptures_sent.gsims               196         
count_eff_ruptures_sent.monitor             2,192       
count_eff_ruptures_sent.sitecol             1,676       
count_eff_ruptures_sent.sources             3,832       
count_eff_ruptures_tot_received             2,644       
hazard.input_weight                         213         
hazard.n_imts                               1           
hazard.n_levels                             19          
hazard.n_realizations                       1           
hazard.n_sites                              13          
hazard.n_sources                            2           
hazard.output_weight                        247         
hostname                                    gem-tstation
require_epsilons                            1           
=========================================== ============

Exposure model
--------------
=============== ========
#assets         13      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 0.0    1   1   4         4         
DS       1.000 0.0    1   1   2         2         
UFB      1.000 0.0    1   1   2         2         
W        1.000 0.0    1   1   5         5         
*ALL*    1.000 0.0    1   1   13        13        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      232       AreaSource   1,612        0.0       11        0        
0      225       AreaSource   520          0.0       3         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       2     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.002 3.308E-04 0.002 0.002 2        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   1.072     0.0       1     
filtering composite source model 0.009     0.0       1     
reading exposure                 0.005     0.0       1     
total count_eff_ruptures         0.004     1.770     2     
managing sources                 0.002     0.0       1     
store source_info                4.497E-04 0.0       1     
aggregate curves                 3.457E-05 0.0       2     
saving probability maps          2.384E-05 0.0       1     
reading site collection          1.359E-05 0.0       1     
================================ ========= ========= ======