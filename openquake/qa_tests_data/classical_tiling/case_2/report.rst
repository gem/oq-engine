Classical Tiling for Turkey reduced
===================================

gem-tstation:/home/michele/ssd/calc_40608.hdf5 updated Mon Aug 22 12:34:11 2016

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
engine_version               '2.1.0-git8cbb23e'                                                                                                                                                                               
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
========================= ====== ==================== =========== ============ ======
source_model              grp_id trt                  num_sources eff_ruptures weight
========================= ====== ==================== =========== ============ ======
models/src/as_model.xml   4      Active Shallow Crust 1           517          96    
models/src/fsbg_model.xml 9      Active Shallow Crust 2           303          51    
========================= ====== ==================== =========== ============ ======

=============== ===
#TRT models     2  
#sources        3  
#eff_ruptures   820
filtered_weight 148
=============== ===

Informational data
------------------
=============================== ============
classical_max_received_per_task 24,635      
classical_num_tasks             15          
classical_sent.monitor          90,735      
classical_sent.rlzs_by_gsim     1,108,872   
classical_sent.sitecol          15,110      
classical_sent.sources          47,286      
classical_tot_received          221,994     
hazard.input_weight             3,360       
hazard.n_imts                   2           
hazard.n_levels                 45          
hazard.n_realizations           3,840       
hazard.n_sites                  83          
hazard.n_sources                31          
hazard.output_weight            28,684,800  
hostname                        gem-tstation
require_epsilons                False       
=============================== ============

Slowest sources
---------------
============ ============ ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id    source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ============ ============ ====== ========= =========== ========== ============= ============= =========
4            AS_GEAS343   AreaSource   96     1         0.016       0.0        23            3.411         9        
9            FSBG_TRBG103 AreaSource   43     1         0.005       0.0        7.219         2.202         4        
9            FSBG_ARAS462 AreaSource   7.650  1         0.002       0.0        0.319         0.164         2        
============ ============ ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.023       0.0        31            5.778         15        3     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  2.070 0.973  0.157 3.414 15       
classical.memory_mb 0.030 0.063  0.0   0.188 15       
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                31        0.188     15    
making contexts                13        0.0       42,516
computing poes                 6.845     0.0       7,380 
managing sources               0.811     0.0       1     
reading composite source model 0.790     0.0       1     
filtering sources              0.327     0.0       279   
reading site collection        0.012     0.0       1     
store source_info              0.006     0.0       1     
saving probability maps        0.003     0.0       1     
aggregate curves               3.159E-04 0.0       15    
============================== ========= ========= ======