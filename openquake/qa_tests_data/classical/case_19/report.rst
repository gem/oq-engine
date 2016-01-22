SHARE OpenQuake Computational Settings
======================================

num_sites = 1, sitecol = 437 B

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           50.0     
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         5.0      
complex_fault_mesh_spacing   5.0      
width_of_mfd_bin             0.2      
area_source_discretization   10.0     
random_seed                  23       
master_seed                  0        
concurrent_tasks             32       
============================ =========

Input files
-----------
======================= ==========================================================================
Name                    File                                                                      
======================= ==========================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_            
job_ini                 `job.ini <job.ini>`_                                                      
source                  `simple_area_source_model.xml <simple_area_source_model.xml>`_            
source_model_logic_tree `simple_source_model_logic_tree.xml <simple_source_model_logic_tree.xml>`_
======================= ==========================================================================

Composite source model
----------------------
========= ====== ============================================================== ====================== ================
smlt_path weight source_model_file                                              gsim_logic_tree        num_realizations
========= ====== ============================================================== ====================== ================
b1        1.0    `simple_area_source_model.xml <simple_area_source_model.xml>`_ complex(4,4,1,0,0,5,2) 160/160         
========= ====== ============================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================================================================== ================= ======================= =================
trt_id gsims                                                                                  distances         siteparams              ruptparams       
====== ====================================================================================== ================= ======================= =================
0      AtkinsonBoore2003SInter LinLee2008SInter YoungsEtAl1997SInter ZhaoEtAl2006SInter       rhypo rrup        vs30                    hypo_depth mag   
1      FaccioliEtAl2010                                                                       rrup              vs30                    rake mag         
2      Campbell2003SHARE ToroEtAl2002SHARE                                                    rjb rrup                                  rake mag         
3      AkkarBommer2010 Campbell2003SHARE CauzziFaccioli2008 ChiouYoungs2008 ToroEtAl2002SHARE rhypo rjb rx rrup vs30measured z1pt0 vs30 ztor mag rake dip
4      AtkinsonBoore2003SSlab LinLee2008SSlab YoungsEtAl1997SSlab ZhaoEtAl2006SSlab           rhypo rrup        vs30                    hypo_depth mag   
====== ====================================================================================== ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(16)
  0,AtkinsonBoore2003SInter: ['40 realizations']
  0,LinLee2008SInter: ['40 realizations']
  0,YoungsEtAl1997SInter: ['40 realizations']
  0,ZhaoEtAl2006SInter: ['40 realizations']
  1,FaccioliEtAl2010: ['160 realizations']
  2,Campbell2003SHARE: ['80 realizations']
  2,ToroEtAl2002SHARE: ['80 realizations']
  3,AkkarBommer2010: ['32 realizations']
  3,Campbell2003SHARE: ['32 realizations']
  3,CauzziFaccioli2008: ['32 realizations']
  3,ChiouYoungs2008: ['32 realizations']
  3,ToroEtAl2002SHARE: ['32 realizations']
  4,AtkinsonBoore2003SSlab: ['40 realizations']
  4,LinLee2008SSlab: ['40 realizations']
  4,YoungsEtAl1997SSlab: ['40 realizations']
  4,ZhaoEtAl2006SSlab: ['40 realizations']>

Number of ruptures per tectonic region type
-------------------------------------------
============================ ====== ==================== =========== ============ ======
source_model                 trt_id trt                  num_sources num_ruptures weight
============================ ====== ==================== =========== ============ ======
simple_area_source_model.xml 0      Subduction Interface 42624       42624        0     
simple_area_source_model.xml 1      Volcanic             210         210          0     
simple_area_source_model.xml 2      Shield               96804       96804        0     
simple_area_source_model.xml 3      Stable Shallow Crust 81154       81154        0     
simple_area_source_model.xml 4      Subduction Inslab    93219       93219        194.25
============================ ====== ==================== =========== ============ ======

=============== ======
#TRT models     5     
#sources        1     
#ruptures       314011
filtered_weight 194.25
=============== ======

Expected data transfer for the sources
--------------------------------------
=========================== ========
Number of tasks to generate 1       
Sent data                   53.14 KB
Total received data         2.53 KB 
Maximum received per task   2.53 KB 
=========================== ========