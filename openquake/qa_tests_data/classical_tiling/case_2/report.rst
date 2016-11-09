Classical Tiling for Turkey reduced
===================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_67022.hdf5 Wed Nov  9 08:16:44 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 83, sitecol = 4.42 KB

Parameters
----------
============================ =================================================================================================================================================================================================
calculation_mode             'classical'                                                                                                                                                                                      
number_of_logic_tree_samples 0                                                                                                                                                                                                
maximum_distance             {u'Volcanic': 100.0, u'Shield': 100.0, u'Active Shallow Crust': 100.0, u'Subduction Interface': 100.0, u'Stable Shallow Crust': 100.0, u'Subduction Deep': 100.0, u'Subduction IntraSlab': 100.0}
investigation_time           10.0                                                                                                                                                                                             
ses_per_logic_tree_path      1                                                                                                                                                                                                
truncation_level             3.0                                                                                                                                                                                              
rupture_mesh_spacing         15.0                                                                                                                                                                                             
complex_fault_mesh_spacing   15.0                                                                                                                                                                                             
width_of_mfd_bin             0.1                                                                                                                                                                                              
area_source_discretization   25.0                                                                                                                                                                                             
random_seed                  323                                                                                                                                                                                              
master_seed                  0                                                                                                                                                                                                
sites_per_tile               10                                                                                                                                                                                               
============================ =================================================================================================================================================================================================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job.ini <job.ini>`_                                                      
site_model               `site_model.xml <site_model.xml>`_                                        
source                   `as_model.xml <as_model.xml>`_                                            
source                   `fsbg_model.xml <fsbg_model.xml>`_                                        
source                   `ss_model.xml <ss_model.xml>`_                                            
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
======================== ====== ======================================================== ====================== ================
smlt_path                weight source_model_file                                        gsim_logic_tree        num_realizations
======================== ====== ======================================================== ====================== ================
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     complex(1,2,5,0,4,4,4) 4/4             
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ complex(1,2,5,0,4,4,4) 4/4             
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     complex(1,2,5,0,4,4,4) 0/0             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
4      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
9      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
====== ========================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  4,AkkarBommer2010(): ['<0,AreaSource~AkkarBommer2010asc_@_@_@_@_@_@,w=0.249999998936>']
  4,CauzziFaccioli2008(): ['<1,AreaSource~CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.249999998936>']
  4,ChiouYoungs2008(): ['<2,AreaSource~ChiouYoungs2008asc_@_@_@_@_@_@,w=0.142857142249>']
  4,ZhaoEtAl2006Asc(): ['<3,AreaSource~ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.0714285711245>']
  9,AkkarBommer2010(): ['<4,FaultSourceAndBackground~AkkarBommer2010asc_@_@_@_@_@_@,w=0.100000001064>']
  9,CauzziFaccioli2008(): ['<5,FaultSourceAndBackground~CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.100000001064>']
  9,ChiouYoungs2008(): ['<6,FaultSourceAndBackground~ChiouYoungs2008asc_@_@_@_@_@_@,w=0.0571428577511>']
  9,ZhaoEtAl2006Asc(): ['<7,FaultSourceAndBackground~ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.0285714288755>']>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== =========== ============ ============
source_model              grp_id trt                  num_sources eff_ruptures tot_ruptures
========================= ====== ==================== =========== ============ ============
models/src/as_model.xml   4      Active Shallow Crust 1           3876         3,876       
models/src/fsbg_model.xml 9      Active Shallow Crust 2           2061         2,061       
========================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      3    
#eff_ruptures 5,937
#tot_ruptures 5,937
#tot_weight   593  
============= =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 2,187       
count_eff_ruptures_num_tasks             4           
count_eff_ruptures_sent.gsims            1,240       
count_eff_ruptures_sent.monitor          7,836       
count_eff_ruptures_sent.sitecol          19,736      
count_eff_ruptures_sent.sources          22,603      
count_eff_ruptures_tot_received          8,748       
hazard.input_weight                      593         
hazard.n_imts                            2           
hazard.n_levels                          90          
hazard.n_realizations                    3,840       
hazard.n_sites                           83          
hazard.n_sources                         3           
hazard.output_weight                     28,684,800  
hostname                                 gem-tstation
require_epsilons                         False       
======================================== ============

Slowest sources
---------------
====== ============ ============ ============ ========= ========= =========
grp_id source_id    source_class num_ruptures calc_time num_sites num_split
====== ============ ============ ============ ========= ========= =========
9      FSBG_ARAS462 AreaSource   306          0.0       4         0        
4      AS_GEAS343   AreaSource   3,876        0.0       40        0        
9      FSBG_TRBG103 AreaSource   1,755        0.0       34        0        
====== ============ ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       3     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ========= ========= ===== =========
operation-duration mean  stddev    min       max   num_tasks
count_eff_ruptures 0.001 2.601E-04 7.920E-04 0.001 4        
================== ===== ========= ========= ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.796     0.0       1     
managing sources                 0.069     0.0       1     
split/filter heavy sources       0.066     0.0       1     
reading site collection          0.024     0.0       1     
filtering composite source model 0.023     0.0       1     
total count_eff_ruptures         0.004     0.0       4     
store source_info                4.289E-04 0.0       1     
aggregate curves                 5.507E-05 0.0       4     
saving probability maps          2.289E-05 0.0       1     
================================ ========= ========= ======