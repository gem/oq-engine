QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_48472.hdf5 Wed Sep  7 16:06:21 2016
engine_version                                 2.1.0-gitfaa2965        
hazardlib_version                              0.21.0-git89bccaf       
============================================== ========================

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
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== ================= =========== ======================= =================

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
======================================== ============
count_eff_ruptures_max_received_per_task 1,516       
count_eff_ruptures_num_tasks             5           
count_eff_ruptures_sent.gsims            445         
count_eff_ruptures_sent.monitor          6,458       
count_eff_ruptures_sent.sitecol          2,841       
count_eff_ruptures_sent.sources          78,271      
count_eff_ruptures_tot_received          7,557       
hazard.input_weight                      817         
hazard.n_imts                            2           
hazard.n_levels                          38          
hazard.n_realizations                    1           
hazard.n_sites                           2           
hazard.n_sources                         4           
hazard.output_weight                     76          
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class       weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
0            3         SimpleFaultSource  617    83        0.0         0.046      0.0           0.0           0        
0            4         ComplexFaultSource 164    0         0.001       0.0        0.0           0.0           0        
0            2         AreaSource         36     0         8.399E-04   0.0        0.0           0.0           0        
0            1         PointSource        0.375  0         5.889E-05   0.0        0.0           0.0           0        
============ ========= ================== ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================== =========== ========== ============= ============= ========= ======
source_class       filter_time split_time cum_calc_time max_calc_time num_tasks counts
================== =========== ========== ============= ============= ========= ======
AreaSource         8.399E-04   0.0        0.0           0.0           0         1     
ComplexFaultSource 0.001       0.0        0.0           0.0           0         1     
PointSource        5.889E-05   0.0        0.0           0.0           0         1     
SimpleFaultSource  0.0         0.046      0.0           0.0           0         1     
================== =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ========= ===== =========
operation-duration mean  stddev min       max   num_tasks
count_eff_ruptures 0.001 0.001  5.538E-04 0.003 5        
================== ===== ====== ========= ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.059     0.0       1     
reading composite source model 0.035     0.0       1     
total count_eff_ruptures       0.006     0.0       5     
filtering sources              0.002     0.0       3     
aggregate curves               7.010E-05 0.0       5     
reading site collection        3.195E-05 0.0       1     
saving probability maps        2.003E-05 0.0       1     
store source_info              7.153E-06 0.0       1     
============================== ========= ========= ======