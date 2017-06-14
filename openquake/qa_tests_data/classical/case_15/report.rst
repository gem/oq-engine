Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29220.hdf5 Wed Jun 14 10:04:15 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 3, num_imts = 2

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
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
source                  `3.0 1.0 <3.0 1.0>`_                                        
source                  `3.2 0.8 <3.2 0.8>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ====== ========================================== =============== ================
smlt_path      weight source_model_file                          gsim_logic_tree num_realizations
============== ====== ========================================== =============== ================
SM1            0.500  `source_model_1.xml <source_model_1.xml>`_ complex(2,2)    4/4             
SM2_a3b1       0.250  `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    2/2             
SM2_a3pt2b0pt8 0.250  `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    2/2             
============== ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =========================================== ========= ========== =================
grp_id gsims                                       distances siteparams ruptparams       
====== =========================================== ========= ========== =================
0      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
1      Campbell2003() ToroEtAl2002()               rjb rrup             mag              
2      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
3      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
====== =========================================== ========= ========== =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): ['<0,SM1~BA2008_C2003,w=0.125>', '<1,SM1~BA2008_T2002,w=0.125>']
  0,CampbellBozorgnia2008(): ['<2,SM1~CB2008_C2003,w=0.125>', '<3,SM1~CB2008_T2002,w=0.125>']
  1,Campbell2003(): ['<0,SM1~BA2008_C2003,w=0.125>', '<2,SM1~CB2008_C2003,w=0.125>']
  1,ToroEtAl2002(): ['<1,SM1~BA2008_T2002,w=0.125>', '<3,SM1~CB2008_T2002,w=0.125>']
  2,BooreAtkinson2008(): ['<4,SM2_a3b1~BA2008_@,w=0.125>']
  2,CampbellBozorgnia2008(): ['<5,SM2_a3b1~CB2008_@,w=0.125>']
  3,BooreAtkinson2008(): ['<6,SM2_a3pt2b0pt8~BA2008_@,w=0.125>']
  3,CampbellBozorgnia2008(): ['<7,SM2_a3pt2b0pt8~CB2008_@,w=0.125>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ======================== =========== ============ ============
source_model       grp_id trt                      num_sources eff_ruptures tot_ruptures
================== ====== ======================== =========== ============ ============
source_model_1.xml 0      Active Shallow Crust     1           15           15          
source_model_1.xml 1      Stable Continental Crust 1           15           15          
source_model_2.xml 2      Active Shallow Crust     1           240          240         
source_model_2.xml 3      Active Shallow Crust     1           240          240         
================== ====== ======================== =========== ============ ============

============= ===
#TRT models   4  
#sources      4  
#eff_ruptures 510
#tot_ruptures 510
#tot_weight   0  
============= ===

Informational data
------------------
============================== ============================================================================
count_eff_ruptures.received    tot 2.26 KB, max_per_task 579 B                                             
count_eff_ruptures.sent        sources 6 KB, param 3.08 KB, srcfilter 2.89 KB, monitor 1.22 KB, gsims 730 B
hazard.input_weight            51                                                                          
hazard.n_imts                  2 B                                                                         
hazard.n_levels                17 B                                                                        
hazard.n_realizations          12 B                                                                        
hazard.n_sites                 3 B                                                                         
hazard.n_sources               4 B                                                                         
hazard.output_weight           102                                                                         
hostname                       tstation.gem.lan                                                            
require_epsilons               0 B                                                                         
============================== ============================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
3      1         AreaSource   240          0.002     3         1        
2      1         AreaSource   240          0.001     3         1        
1      2         PointSource  15           1.957E-04 3         1        
0      1         PointSource  15           1.876E-04 3         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.003     2     
PointSource  3.834E-04 2     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.002 8.185E-04 0.001 0.003 4        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.010     0.0       1     
total count_eff_ruptures       0.007     0.0       4     
store source_info              0.005     0.0       1     
managing sources               0.004     0.0       1     
prefiltering source model      0.002     0.0       1     
aggregate curves               8.893E-05 0.0       4     
reading site collection        4.721E-05 0.0       1     
saving probability maps        3.219E-05 0.0       1     
============================== ========= ========= ======