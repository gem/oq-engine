Event-based PSHA producing hazard curves only
=============================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66999.hdf5 Wed Nov  9 08:15:59 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'event_based'                   
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      300                             
truncation_level             3.0                             
rupture_mesh_spacing         2.0                             
complex_fault_mesh_spacing   2.0                             
width_of_mfd_bin             0.2                             
area_source_discretization   20.0                            
random_seed                  23                              
master_seed                  0                               
============================ ================================

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
b11       0.600  `source_model1.xml <source_model1.xml>`_ simple(3)       3/3             
b12       0.400  `source_model2.xml <source_model2.xml>`_ simple(3)       3/3             
========= ====== ======================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ============================= =================
grp_id gsims                                                         distances   siteparams                    ruptparams       
====== ============================================================= =========== ============================= =================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
1      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
====== ============================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,BooreAtkinson2008(): ['<0,b11~b11,w=0.30000000298>']
  0,CampbellBozorgnia2008(): ['<1,b11~b12,w=0.180000001788>']
  0,ChiouYoungs2008(): ['<2,b11~b13,w=0.120000001192>']
  1,BooreAtkinson2008(): ['<3,b12~b11,w=0.19999999702>']
  1,CampbellBozorgnia2008(): ['<4,b12~b12,w=0.119999998212>']
  1,ChiouYoungs2008(): ['<5,b12~b13,w=0.0799999988079>']>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ============
source_model      grp_id trt                  num_sources eff_ruptures tot_ruptures
================= ====== ==================== =========== ============ ============
source_model1.xml 0      Active Shallow Crust 1           2144         2,456       
source_model2.xml 1      Active Shallow Crust 1           937          2,456       
================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      2    
#eff_ruptures 3,081
#tot_ruptures 4,912
#tot_weight   491  
============= =====

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 1,907,397   
compute_ruptures_num_tasks             4           
compute_ruptures_sent.gsims            1,016       
compute_ruptures_sent.monitor          4,120       
compute_ruptures_sent.sitecol          2,308       
compute_ruptures_sent.sources          180,192     
compute_ruptures_tot_received          3,330,595   
hazard.input_weight                    491         
hazard.n_imts                          1           
hazard.n_levels                        5           
hazard.n_realizations                  6           
hazard.n_sites                         1           
hazard.n_sources                       2           
hazard.output_weight                   900         
hostname                               gem-tstation
====================================== ============

Specific information for event based
------------------------------------
======================== ======
Total number of ruptures 3,081 
Total number of events   16,186
Rupture multiplicity     5.253 
======================== ======

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      1         AreaSource   2,456        0.0       1         0        
0      1         AreaSource   2,456        0.0       1         0        
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
compute_ruptures   0.935 0.611  0.353 1.615 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           3.741     5.309     4     
filtering ruptures               0.754     0.0       3,081 
managing sources                 0.531     0.0       1     
split/filter heavy sources       0.528     0.0       2     
reading composite source model   0.156     0.0       1     
saving ruptures                  0.093     0.0       4     
filtering composite source model 0.002     0.0       1     
store source_info                5.782E-04 0.0       1     
reading site collection          4.005E-05 0.0       1     
================================ ========= ========= ======