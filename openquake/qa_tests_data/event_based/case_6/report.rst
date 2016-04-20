Event-based PSHA producing hazard curves only
=============================================

Datastore /home/michele/ssd/calc_11446.hdf5 last updated Wed Apr 20 09:38:53 2016 on gem-tstation

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'event_based'      
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      300                
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             0.2                
area_source_discretization   20.0               
random_seed                  23                 
master_seed                  0                  
oqlite_version               '0.13.0-git361357f'
============================ ===================

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
====== ======================================================= =========== ============================= =================
trt_id gsims                                                   distances   siteparams                    ruptparams       
====== ======================================================= =========== ============================= =================
0      BooreAtkinson2008 CampbellBozorgnia2008 ChiouYoungs2008 rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
1      BooreAtkinson2008 CampbellBozorgnia2008 ChiouYoungs2008 rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
====== ======================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,BooreAtkinson2008: ['<0,b11,b11,w=0.3>']
  0,CampbellBozorgnia2008: ['<1,b11,b12,w=0.18>']
  0,ChiouYoungs2008: ['<2,b11,b13,w=0.12>']
  1,BooreAtkinson2008: ['<3,b12,b11,w=0.2>']
  1,CampbellBozorgnia2008: ['<4,b12,b12,w=0.12>']
  1,ChiouYoungs2008: ['<5,b12,b13,w=0.08>']>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ======
source_model      trt_id trt                  num_sources eff_ruptures weight
================= ====== ==================== =========== ============ ======
source_model1.xml 0      Active Shallow Crust 1           2,144        61    
source_model2.xml 1      Active Shallow Crust 1           937          61    
================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   3,081
filtered_weight 122  
=============== =====

Informational data
------------------
======== ==============
hostname 'gem-tstation'
======== ==============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   61     307       0.001       0.065      4.267    
1            1         AreaSource   61     307       0.001       0.065      2.951    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_gmfs_and_curves  8.418     0.109     41    
total compute_ruptures         7.254     0.0       62    
compute poes                   5.551     0.0       3,081 
make contexts                  2.706     0.0       3,081 
filtering ruptures             1.436     0.0       3,081 
saving ruptures                0.871     0.0       1     
managing sources               0.298     0.0       1     
reading composite source model 0.140     0.0       1     
splitting sources              0.130     0.0       2     
bulding hazard curves          0.109     0.0       41    
aggregating hcurves            0.103     0.0       123   
aggregate curves               0.029     0.0       185   
store source_info              0.009     0.0       1     
filtering sources              0.003     0.0       2     
reading site collection        4.411E-05 0.0       1     
============================== ========= ========= ======