Classical PSHA QA test with sites_csv
=====================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29235.hdf5 Wed Jun 14 10:04:33 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 10, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
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
sites                   `qa_sites.csv <qa_sites.csv>`_                              
source                  `simple_fault.xml <simple_fault.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============ ====== ====================================== =============== ================
smlt_path    weight source_model_file                      gsim_logic_tree num_realizations
============ ====== ====================================== =============== ================
simple_fault 1.000  `simple_fault.xml <simple_fault.xml>`_ simple(2)       2/2             
============ ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================= =========== ============================= =======================
grp_id gsims                                         distances   siteparams                    ruptparams             
====== ============================================= =========== ============================= =======================
0      AbrahamsonSilva2008() CampbellBozorgnia2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake width ztor
====== ============================================= =========== ============================= =======================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AbrahamsonSilva2008(): ['<0,simple_fault~AbrahamsonSilva2008,w=0.5>']
  0,CampbellBozorgnia2008(): ['<1,simple_fault~CampbellBozorgnia2008,w=0.5>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
simple_fault.xml 0      Active Shallow Crust 1           447          447         
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== =============================================================================
count_eff_ruptures.received    tot 1.93 KB, max_per_task 720 B                                              
count_eff_ruptures.sent        sources 5.06 KB, srcfilter 2.74 KB, param 2.01 KB, monitor 939 B, gsims 585 B
hazard.input_weight            447                                                                          
hazard.n_imts                  1 B                                                                          
hazard.n_levels                13 B                                                                         
hazard.n_realizations          2 B                                                                          
hazard.n_sites                 10 B                                                                         
hazard.n_sources               1 B                                                                          
hazard.output_weight           130                                                                          
hostname                       tstation.gem.lan                                                             
require_epsilons               0 B                                                                          
============================== =============================================================================

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
0      3         SimpleFaultSource 447          0.045     10        15       
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.045     1     
================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.016 0.009  0.010 0.026 3        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.059     0.0       1     
total count_eff_ruptures       0.047     0.0       3     
reading composite source model 0.005     0.0       1     
store source_info              0.004     0.0       1     
prefiltering source model      0.002     0.0       1     
reading site collection        2.296E-04 0.0       1     
aggregate curves               7.820E-05 0.0       3     
saving probability maps        3.290E-05 0.0       1     
============================== ========= ========= ======