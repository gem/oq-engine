Classical PSHA QA test with sites_csv
=====================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_80562.hdf5 Thu Jan 26 05:25:28 2017
engine_version                                 2.3.0-gitd31dc69        
hazardlib_version                              0.23.0-git4d14bee       
============================================== ========================

num_sites = 10, sitecol = 1.15 KB

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
width_of_mfd_bin                0.1                            
area_source_discretization      10.0                           
ground_motion_correlation_model None                           
random_seed                     23                             
master_seed                     0                              
sites_per_tile                  10000                          
=============================== ===============================

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
0      AbrahamsonSilva2008() CampbellBozorgnia2008() rrup rx rjb z1pt0 vs30 vs30measured z2pt5 mag width dip rake ztor
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
=========================================== ============
count_eff_ruptures_max_received_per_task    1,296       
count_eff_ruptures_num_tasks                3           
count_eff_ruptures_sent.gsims               585         
count_eff_ruptures_sent.monitor             3,222       
count_eff_ruptures_sent.sitecol             2,334       
count_eff_ruptures_sent.sources             5,177       
count_eff_ruptures_tot_received             3,888       
hazard.input_weight                         447         
hazard.n_imts                               1           
hazard.n_levels                             13          
hazard.n_realizations                       2           
hazard.n_sites                              10          
hazard.n_sources                            1           
hazard.output_weight                        260         
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

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
count_eff_ruptures 8.782E-04 7.789E-05 7.975E-04 9.530E-04 3        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
managing sources                 0.085     0.0       1     
split/filter heavy sources       0.083     0.0       1     
reading composite source model   0.009     0.0       1     
filtering composite source model 0.003     0.0       1     
total count_eff_ruptures         0.003     0.0       3     
store source_info                7.150E-04 0.0       1     
reading site collection          1.853E-04 0.0       1     
aggregate curves                 5.531E-05 0.0       3     
saving probability maps          3.314E-05 0.0       1     
================================ ========= ========= ======