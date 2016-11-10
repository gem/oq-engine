Classical PSHA QA test with sites_csv
=====================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66987.hdf5 Wed Nov  9 08:15:23 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 10, sitecol = 1.13 KB

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         2.0                             
complex_fault_mesh_spacing   2.0                             
width_of_mfd_bin             0.1                             
area_source_discretization   10.0                            
random_seed                  23                              
master_seed                  0                               
sites_per_tile               10000                           
============================ ================================

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
0      AbrahamsonSilva2008() CampbellBozorgnia2008() rx rjb rrup vs30measured vs30 z2pt5 z1pt0 rake width ztor mag dip
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
======================================== ============
count_eff_ruptures_max_received_per_task 1,336       
count_eff_ruptures_num_tasks             3           
count_eff_ruptures_sent.gsims            552         
count_eff_ruptures_sent.monitor          3,291       
count_eff_ruptures_sent.sitecol          2,487       
count_eff_ruptures_sent.sources          5,360       
count_eff_ruptures_tot_received          4,008       
hazard.input_weight                      447         
hazard.n_imts                            1           
hazard.n_levels                          13          
hazard.n_realizations                    2           
hazard.n_sites                           10          
hazard.n_sources                         1           
hazard.output_weight                     260         
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
0      3         SimpleFaultSource 447          0.0       10        0        
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.0       1     
================= ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 8.346E-04 4.840E-05 7.861E-04 8.829E-04 3        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
managing sources                 0.078     0.0       1     
split/filter heavy sources       0.076     0.0       1     
reading composite source model   0.007     0.0       1     
filtering composite source model 0.003     0.0       1     
total count_eff_ruptures         0.003     0.0       3     
store source_info                7.081E-04 0.0       1     
reading site collection          8.798E-05 0.0       1     
aggregate curves                 5.603E-05 0.0       3     
saving probability maps          3.099E-05 0.0       1     
================================ ========= ========= ======