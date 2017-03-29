Event-based PSHA with logic tree sampling
=========================================

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85588.hdf5 Tue Feb 14 15:48:25 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

num_sites = 3, sitecol = 917 B

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    10                
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         40                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================== =============== ================
smlt_path weight source_model_file                        gsim_logic_tree num_realizations
========= ====== ======================================== =============== ================
b11       0.100  `source_model1.xml <source_model1.xml>`_ simple(3)       7/3             
b12       0.100  `source_model2.xml <source_model2.xml>`_ simple(3)       3/3             
========= ====== ======================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ============================= =================
grp_id gsims                                                         distances   siteparams                    ruptparams       
====== ============================================================= =========== ============================= =================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rrup rjb rx vs30 z1pt0 vs30measured z2pt5 mag dip rake ztor
1      BooreAtkinson2008() CampbellBozorgnia2008()                   rrup rjb    vs30 z2pt5                    mag dip rake ztor
====== ============================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)
  0,BooreAtkinson2008(): ['<3,b11~BA,w=0.1>', '<5,b11~BA,w=0.1>']
  0,CampbellBozorgnia2008(): ['<4,b11~CB,w=0.1>', '<6,b11~CB,w=0.1>']
  0,ChiouYoungs2008(): ['<0,b11~CY,w=0.1>', '<1,b11~CY,w=0.1>', '<2,b11~CY,w=0.1>']
  1,BooreAtkinson2008(): ['<8,b12~BA,w=0.1>', '<9,b12~BA,w=0.1>']
  1,CampbellBozorgnia2008(): ['<7,b12~CB,w=0.1>']>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ============
source_model      grp_id trt                  num_sources eff_ruptures tot_ruptures
================= ====== ==================== =========== ============ ============
source_model1.xml 0      Active Shallow Crust 1           2120         2,456       
source_model2.xml 1      Active Shallow Crust 1           478          2,456       
================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      2    
#eff_ruptures 2,598
#tot_ruptures 4,912
#tot_weight   491  
============= =====

Informational data
------------------
========================================= ============
compute_ruptures_max_received_per_task    1,784,075   
compute_ruptures_num_tasks                4           
compute_ruptures_sent.gsims               916         
compute_ruptures_sent.monitor             5,644       
compute_ruptures_sent.sources             167,590     
compute_ruptures_sent.src_filter          3,064       
compute_ruptures_tot_received             2,681,886   
hazard.input_weight                       2,456       
hazard.n_imts                             2           
hazard.n_levels                           38          
hazard.n_realizations                     10          
hazard.n_sites                            3           
hazard.n_sources                          2           
hazard.output_weight                      1,200       
hostname                                  gem-tstation
require_epsilons                          False       
========================================= ============

Specific information for event based
------------------------------------
======================== ======
Total number of ruptures 2,598 
Total number of events   14,308
Rupture multiplicity     5.507 
======================== ======

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         AreaSource   2,456        0.0       3         0        
1      1         AreaSource   2,456        0.0       3         0        
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
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.838 0.622  0.269 1.651 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           3.353     1.102     4     
filtering ruptures               0.706     0.0       2,598 
managing sources                 0.536     0.0       1     
setting event years              0.206     0.0       1     
reading composite source model   0.151     0.0       1     
saving ruptures                  0.106     0.0       4     
filtering composite source model 0.002     0.0       1     
store source_info                5.546E-04 0.0       1     
reading site collection          5.388E-05 0.0       1     
================================ ========= ========= ======