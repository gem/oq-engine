Classical PSHA QA test with sites_csv
=====================================

gem-tstation:/home/michele/ssd/calc_40718.hdf5 updated Mon Aug 22 12:53:29 2016

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
engine_version               '2.1.0-git8cbb23e'              
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
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
simple_fault.xml 0      Active Shallow Crust 1           447          447   
================ ====== ==================== =========== ============ ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 4,467       
classical_num_tasks             12          
classical_sent.monitor          10,680      
classical_sent.rlzs_by_gsim     9,204       
classical_sent.sitecol          7,356       
classical_sent.sources          13,651      
classical_tot_received          53,300      
hazard.input_weight             447         
hazard.n_imts                   1           
hazard.n_levels                 13          
hazard.n_realizations           2           
hazard.n_sites                  10          
hazard.n_sources                1           
hazard.output_weight            260         
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class      weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
0            3         SimpleFaultSource 447    15        0.002       0.037      2.848         0.313         15       
============ ========= ================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
SimpleFaultSource 0.002       0.037      2.848         0.313         15        1     
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  0.241 0.064  0.107 0.316 12       
classical.memory_mb 0.0   0.0    0.0   0.0   12       
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                2.886     0.0       12    
making contexts                2.065     0.0       447   
computing poes                 0.590     0.0       447   
managing sources               0.056     0.0       1     
splitting sources              0.037     0.0       1     
reading composite source model 0.008     0.0       1     
store source_info              0.006     0.0       1     
filtering sources              0.002     0.0       1     
read poes                      0.002     0.0       1     
saving probability maps        0.001     0.0       1     
aggregate curves               8.011E-04 0.0       12    
reading site collection        1.049E-04 0.0       1     
============================== ========= ========= ======