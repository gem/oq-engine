QA test for disaggregation case_1, taken from the disagg demo
=============================================================

gem-tstation:/home/michele/ssd/calc_40607.hdf5 updated Mon Aug 22 12:34:05 2016

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ================================
calculation_mode             'disaggregation'                
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         5.0                             
complex_fault_mesh_spacing   5.0                             
width_of_mfd_bin             0.2                             
area_source_discretization   10.0                            
random_seed                  9000                            
master_seed                  0                               
engine_version               '2.1.0-git8cbb23e'              
============================ ================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== =========== ======================= =================
grp_id gsims                 distances   siteparams              ruptparams       
====== ===================== =========== ======================= =================
0      ['ChiouYoungs2008()'] rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== ===================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 4           2236         817   
================ ====== ==================== =========== ============ ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 8,424       
classical_num_tasks             5           
classical_sent.monitor          27,445      
classical_sent.rlzs_by_gsim     2,615       
classical_sent.sitecol          2,265       
classical_sent.sources          78,271      
classical_tot_received          37,416      
hazard.input_weight             817         
hazard.n_imts                   2           
hazard.n_levels                 19          
hazard.n_realizations           1           
hazard.n_sites                  2           
hazard.n_sources                4           
hazard.output_weight            76          
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class       weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
0            2         AreaSource         36     1         9.100E-04   0.0        1.877         1.877         1        
0            3         SimpleFaultSource  617    83        0.002       0.044      1.138         0.180         83       
0            4         ComplexFaultSource 164    1         0.001       0.0        0.386         0.386         1        
0            1         PointSource        0.375  1         5.507E-05   0.0        0.041         0.041         1        
============ ========= ================== ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================== =========== ========== ============= ============= ========= ======
source_class       filter_time split_time cum_calc_time max_calc_time num_tasks counts
================== =========== ========== ============= ============= ========= ======
AreaSource         9.100E-04   0.0        1.877         1.877         1         1     
ComplexFaultSource 0.001       0.0        0.386         0.386         1         1     
PointSource        5.507E-05   0.0        0.041         0.041         1         1     
SimpleFaultSource  0.002       0.044      1.138         0.180         83        1     
================== =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  0.693 0.906  0.151 2.307 5        
classical.memory_mb 0.0   0.0    0.0   0.0   5        
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                3.463     0.0       5     
making contexts                1.598     0.0       2,236 
computing poes                 0.901     0.0       2,236 
get closest points             0.328     0.0       2,236 
managing sources               0.062     0.0       1     
splitting sources              0.044     0.0       1     
reading composite source model 0.039     0.0       1     
store source_info              0.014     0.0       1     
filtering sources              0.005     0.0       4     
saving probability maps        0.003     0.0       1     
aggregate curves               7.770E-04 0.0       5     
reading site collection        3.982E-05 0.0       1     
============================== ========= ========= ======