Event-based PSHA with logic tree sampling
=========================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29257.hdf5 Wed Jun 14 10:04:54 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 3, num_imts = 2

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
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
1      BooreAtkinson2008() CampbellBozorgnia2008()                   rjb rrup    vs30 z2pt5                    dip mag rake ztor
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
source_model1.xml 0      Active Shallow Crust 1           2456         2,456       
source_model2.xml 1      Active Shallow Crust 1           2456         2,456       
================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      2    
#eff_ruptures 4,912
#tot_ruptures 4,912
#tot_weight   0    
============= =====

Informational data
------------------
============================ ==================================================================================
compute_ruptures.received    tot 2.1 MB, max_per_task 1.41 MB                                                  
compute_ruptures.sent        sources 163.66 KB, param 3.76 KB, src_filter 2.89 KB, monitor 1.21 KB, gsims 916 B
hazard.input_weight          2,456                                                                             
hazard.n_imts                2 B                                                                               
hazard.n_levels              38 B                                                                              
hazard.n_realizations        10 B                                                                              
hazard.n_sites               3 B                                                                               
hazard.n_sources             2 B                                                                               
hazard.output_weight         360                                                                               
hostname                     tstation.gem.lan                                                                  
require_epsilons             0 B                                                                               
============================ ==================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      1         AreaSource   2,456        0.0       3         0        
0      1         AreaSource   2,456        0.0       3         0        
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
compute_ruptures   0.852 0.616  0.286 1.646 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         3.407     2.086     4     
filtering ruptures             0.620     0.0       2,598 
managing sources               0.186     0.0       1     
saving ruptures                0.123     0.0       4     
reading composite source model 0.111     0.0       1     
setting event years            0.058     0.0       1     
store source_info              0.005     0.0       1     
prefiltering source model      0.003     0.0       1     
reading site collection        5.269E-05 0.0       1     
============================== ========= ========= ======