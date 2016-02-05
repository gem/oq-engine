Classical Tiling for Turkey reduced
===================================

num_sites = 83, sitecol = 4.37 KB

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             100.0    
investigation_time           10.0     
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         15.0     
complex_fault_mesh_spacing   15.0     
width_of_mfd_bin             0.1      
area_source_discretization   25.0     
random_seed                  323      
master_seed                  0        
concurrent_tasks             4        
sites_per_tile               10       
============================ =========

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
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     simple(0,0,0,0,0,4,0)  4/4             
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ simple(0,0,0,0,0,4,0)  4/4             
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     trivial(0,0,0,0,0,0,0) 0/0             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================== ================= ======================= ============================
trt_id gsims                                                              distances         siteparams              ruptparams                  
====== ================================================================== ================= ======================= ============================
4      AkkarBommer2010 CauzziFaccioli2008 ChiouYoungs2008 ZhaoEtAl2006Asc rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
9      AkkarBommer2010 CauzziFaccioli2008 ChiouYoungs2008 ZhaoEtAl2006Asc rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
====== ================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(8)
  4,AkkarBommer2010: ['<0,AreaSource,AkkarBommer2010asc_@_@_@_@_@_@,w=0.25>']
  4,CauzziFaccioli2008: ['<1,AreaSource,CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.25>']
  4,ChiouYoungs2008: ['<2,AreaSource,ChiouYoungs2008asc_@_@_@_@_@_@,w=0.142857142857>']
  4,ZhaoEtAl2006Asc: ['<3,AreaSource,ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.0714285714286>']
  9,AkkarBommer2010: ['<4,FaultSourceAndBackground,AkkarBommer2010asc_@_@_@_@_@_@,w=0.1>']
  9,CauzziFaccioli2008: ['<5,FaultSourceAndBackground,CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.1>']
  9,ChiouYoungs2008: ['<6,FaultSourceAndBackground,ChiouYoungs2008asc_@_@_@_@_@_@,w=0.0571428571429>']
  9,ZhaoEtAl2006Asc: ['<7,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.0285714285714>']>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== =========== ============ =============
source_model              trt_id trt                  num_sources eff_ruptures weight       
========================= ====== ==================== =========== ============ =============
models/src/as_model.xml   4      Active Shallow Crust 1           31008        96.9000015259
models/src/fsbg_model.xml 9      Active Shallow Crust 2           7326         51.5250000954
========================= ====== ==================== =========== ============ =============

=============== =============
#TRT models     2            
#sources        3            
#eff_ruptures   38334        
filtered_weight 148.425001621
=============== =============

Expected data transfer for the sources
--------------------------------------
=========================== =======
Number of tasks to generate 13     
Sent data                   2.72 MB
=========================== =======

Slowest sources
---------------
============ ============ ============ ====== ========= =========== ========== =========
trt_model_id source_id    source_class weight split_num filter_time split_time calc_time
============ ============ ============ ====== ========= =========== ========== =========
4            AS_GEAS343   AreaSource   96.9   1         0.0203552   0.0        0.0      
9            FSBG_TRBG103 AreaSource   43.875 1         0.00637221  0.0        0.0      
9            FSBG_ARAS462 AreaSource   7.65   1         0.00161386  0.0        0.0      
============ ============ ============ ====== ========= =========== ========== =========