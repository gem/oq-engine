Classical Tiling for Turkey reduced
===================================

num_sites = 83, sitecol = 4.61 KB

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
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     complex(1,2,5,0,4,4,4) 640/640         
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ complex(1,2,5,0,0,4,0) 40/40           
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     simple(0,0,0,0,0,4,0)  4/4             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================================================================== ================= ======================= ============================
trt_id gsims                                                                                  distances         siteparams              ruptparams                  
====== ====================================================================================== ================= ======================= ============================
0      Campbell2003SHARE ToroEtAl2002SHARE                                                    rjb rrup                                  rake mag                    
1      AtkinsonBoore2003SInter LinLee2008SInter YoungsEtAl1997SInter ZhaoEtAl2006SInter       rhypo rrup        vs30                    hypo_depth mag              
2      AtkinsonBoore2003SSlab LinLee2008SSlab YoungsEtAl1997SSlab ZhaoEtAl2006SSlab           rhypo rrup        vs30                    hypo_depth mag              
3      FaccioliEtAl2010                                                                       rrup              vs30                    rake mag                    
4      AkkarBommer2010 CauzziFaccioli2008 ChiouYoungs2008 ZhaoEtAl2006Asc                     rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
5      AkkarBommer2010 Campbell2003SHARE CauzziFaccioli2008 ChiouYoungs2008 ToroEtAl2002SHARE rhypo rjb rx rrup vs30measured z1pt0 vs30 ztor mag rake dip           
6      Campbell2003SHARE ToroEtAl2002SHARE                                                    rjb rrup                                  rake mag                    
7      FaccioliEtAl2010                                                                       rrup              vs30                    rake mag                    
8      AkkarBommer2010 Campbell2003SHARE CauzziFaccioli2008 ChiouYoungs2008 ToroEtAl2002SHARE rhypo rjb rx rrup vs30measured z1pt0 vs30 ztor mag rake dip           
9      AkkarBommer2010 CauzziFaccioli2008 ChiouYoungs2008 ZhaoEtAl2006Asc                     rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
10     AkkarBommer2010 CauzziFaccioli2008 ChiouYoungs2008 ZhaoEtAl2006Asc                     rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
====== ====================================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(36)
  0,Campbell2003SHARE: ['320 realizations']
  0,ToroEtAl2002SHARE: ['320 realizations']
  1,AtkinsonBoore2003SInter: ['160 realizations']
  1,LinLee2008SInter: ['160 realizations']
  1,YoungsEtAl1997SInter: ['160 realizations']
  1,ZhaoEtAl2006SInter: ['160 realizations']
  2,AtkinsonBoore2003SSlab: ['160 realizations']
  2,LinLee2008SSlab: ['160 realizations']
  2,YoungsEtAl1997SSlab: ['160 realizations']
  2,ZhaoEtAl2006SSlab: ['160 realizations']
  3,FaccioliEtAl2010: ['640 realizations']
  4,AkkarBommer2010: ['160 realizations']
  4,CauzziFaccioli2008: ['160 realizations']
  4,ChiouYoungs2008: ['160 realizations']
  4,ZhaoEtAl2006Asc: ['160 realizations']
  5,AkkarBommer2010: ['128 realizations']
  5,Campbell2003SHARE: ['128 realizations']
  5,CauzziFaccioli2008: ['128 realizations']
  5,ChiouYoungs2008: ['128 realizations']
  5,ToroEtAl2002SHARE: ['128 realizations']
  6,Campbell2003SHARE: ['20 realizations']
  6,ToroEtAl2002SHARE: ['20 realizations']
  7,FaccioliEtAl2010: ['40 realizations']
  8,AkkarBommer2010: ['<640,FaultSourceAndBackground,AkkarBommer2010asc_AkkarBommer2010ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<641,FaultSourceAndBackground,AkkarBommer2010asc_AkkarBommer2010ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<650,FaultSourceAndBackground,CauzziFaccioli2008asc_AkkarBommer2010ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<651,FaultSourceAndBackground,CauzziFaccioli2008asc_AkkarBommer2010ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<660,FaultSourceAndBackground,ChiouYoungs2008asc_AkkarBommer2010ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<661,FaultSourceAndBackground,ChiouYoungs2008asc_AkkarBommer2010ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<670,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_AkkarBommer2010ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<671,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_AkkarBommer2010ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>']
  8,Campbell2003SHARE: ['<642,FaultSourceAndBackground,AkkarBommer2010asc_Campbell2003SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<643,FaultSourceAndBackground,AkkarBommer2010asc_Campbell2003SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<652,FaultSourceAndBackground,CauzziFaccioli2008asc_Campbell2003SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<653,FaultSourceAndBackground,CauzziFaccioli2008asc_Campbell2003SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<662,FaultSourceAndBackground,ChiouYoungs2008asc_Campbell2003SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<663,FaultSourceAndBackground,ChiouYoungs2008asc_Campbell2003SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<672,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_Campbell2003SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<673,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_Campbell2003SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>']
  8,CauzziFaccioli2008: ['<644,FaultSourceAndBackground,AkkarBommer2010asc_CauzziFaccioli2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<645,FaultSourceAndBackground,AkkarBommer2010asc_CauzziFaccioli2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<654,FaultSourceAndBackground,CauzziFaccioli2008asc_CauzziFaccioli2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<655,FaultSourceAndBackground,CauzziFaccioli2008asc_CauzziFaccioli2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<664,FaultSourceAndBackground,ChiouYoungs2008asc_CauzziFaccioli2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<665,FaultSourceAndBackground,ChiouYoungs2008asc_CauzziFaccioli2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<674,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_CauzziFaccioli2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<675,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_CauzziFaccioli2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>']
  8,ChiouYoungs2008: ['<646,FaultSourceAndBackground,AkkarBommer2010asc_ChiouYoungs2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<647,FaultSourceAndBackground,AkkarBommer2010asc_ChiouYoungs2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<656,FaultSourceAndBackground,CauzziFaccioli2008asc_ChiouYoungs2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<657,FaultSourceAndBackground,CauzziFaccioli2008asc_ChiouYoungs2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<666,FaultSourceAndBackground,ChiouYoungs2008asc_ChiouYoungs2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<667,FaultSourceAndBackground,ChiouYoungs2008asc_ChiouYoungs2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<676,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_ChiouYoungs2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<677,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_ChiouYoungs2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>']
  8,ToroEtAl2002SHARE: ['<648,FaultSourceAndBackground,AkkarBommer2010asc_Toro2002SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<649,FaultSourceAndBackground,AkkarBommer2010asc_Toro2002SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<658,FaultSourceAndBackground,CauzziFaccioli2008asc_Toro2002SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<659,FaultSourceAndBackground,CauzziFaccioli2008asc_Toro2002SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<668,FaultSourceAndBackground,ChiouYoungs2008asc_Toro2002SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<669,FaultSourceAndBackground,ChiouYoungs2008asc_Toro2002SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<678,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_Toro2002SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<679,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_Toro2002SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>']
  9,AkkarBommer2010: ['<640,FaultSourceAndBackground,AkkarBommer2010asc_AkkarBommer2010ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<641,FaultSourceAndBackground,AkkarBommer2010asc_AkkarBommer2010ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<642,FaultSourceAndBackground,AkkarBommer2010asc_Campbell2003SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<643,FaultSourceAndBackground,AkkarBommer2010asc_Campbell2003SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<644,FaultSourceAndBackground,AkkarBommer2010asc_CauzziFaccioli2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<645,FaultSourceAndBackground,AkkarBommer2010asc_CauzziFaccioli2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<646,FaultSourceAndBackground,AkkarBommer2010asc_ChiouYoungs2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<647,FaultSourceAndBackground,AkkarBommer2010asc_ChiouYoungs2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<648,FaultSourceAndBackground,AkkarBommer2010asc_Toro2002SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<649,FaultSourceAndBackground,AkkarBommer2010asc_Toro2002SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>']
  9,CauzziFaccioli2008: ['<650,FaultSourceAndBackground,CauzziFaccioli2008asc_AkkarBommer2010ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<651,FaultSourceAndBackground,CauzziFaccioli2008asc_AkkarBommer2010ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<652,FaultSourceAndBackground,CauzziFaccioli2008asc_Campbell2003SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<653,FaultSourceAndBackground,CauzziFaccioli2008asc_Campbell2003SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<654,FaultSourceAndBackground,CauzziFaccioli2008asc_CauzziFaccioli2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<655,FaultSourceAndBackground,CauzziFaccioli2008asc_CauzziFaccioli2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<656,FaultSourceAndBackground,CauzziFaccioli2008asc_ChiouYoungs2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<657,FaultSourceAndBackground,CauzziFaccioli2008asc_ChiouYoungs2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<658,FaultSourceAndBackground,CauzziFaccioli2008asc_Toro2002SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>', '<659,FaultSourceAndBackground,CauzziFaccioli2008asc_Toro2002SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.007>']
  9,ChiouYoungs2008: ['<660,FaultSourceAndBackground,ChiouYoungs2008asc_AkkarBommer2010ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<661,FaultSourceAndBackground,ChiouYoungs2008asc_AkkarBommer2010ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<662,FaultSourceAndBackground,ChiouYoungs2008asc_Campbell2003SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<663,FaultSourceAndBackground,ChiouYoungs2008asc_Campbell2003SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<664,FaultSourceAndBackground,ChiouYoungs2008asc_CauzziFaccioli2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<665,FaultSourceAndBackground,ChiouYoungs2008asc_CauzziFaccioli2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<666,FaultSourceAndBackground,ChiouYoungs2008asc_ChiouYoungs2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<667,FaultSourceAndBackground,ChiouYoungs2008asc_ChiouYoungs2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<668,FaultSourceAndBackground,ChiouYoungs2008asc_Toro2002SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>', '<669,FaultSourceAndBackground,ChiouYoungs2008asc_Toro2002SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.004>']
  9,ZhaoEtAl2006Asc: ['<670,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_AkkarBommer2010ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<671,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_AkkarBommer2010ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<672,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_Campbell2003SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<673,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_Campbell2003SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<674,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_CauzziFaccioli2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<675,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_CauzziFaccioli2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<676,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_ChiouYoungs2008ssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<677,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_ChiouYoungs2008ssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<678,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_Toro2002SHAREssc_Campbell2003SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>', '<679,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_Toro2002SHAREssc_Toro2002SHAREshld_@_@_FaccioliEtAl2010vol_@,w=0.002>']
  10,AkkarBommer2010: ['<680,SeiFaCrust,AkkarBommer2010asc_@_@_@_@_@_@,w=0.105>']
  10,CauzziFaccioli2008: ['<681,SeiFaCrust,CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.105>']
  10,ChiouYoungs2008: ['<682,SeiFaCrust,ChiouYoungs2008asc_@_@_@_@_@_@,w=0.06>']
  10,ZhaoEtAl2006Asc: ['<683,SeiFaCrust,ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.03>']>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== =========== ============ =============
source_model              trt_id trt                  num_sources num_ruptures weight       
========================= ====== ==================== =========== ============ =============
models/src/as_model.xml   0      Shield               0           2808         0            
models/src/as_model.xml   1      Subduction Interface 0           334          0            
models/src/as_model.xml   2      Subduction IntraSlab 0           18585        0            
models/src/as_model.xml   3      Volcanic             0           14           0            
models/src/as_model.xml   4      Active Shallow Crust 1           32481        96.9000015259
models/src/as_model.xml   5      Stable Shallow Crust 0           28746        0            
models/src/fsbg_model.xml 6      Shield               0           20124        0            
models/src/fsbg_model.xml 7      Volcanic             0           42           0            
models/src/fsbg_model.xml 8      Stable Shallow Crust 0           1572         0            
models/src/fsbg_model.xml 9      Active Shallow Crust 2           16635        51.5250000954
models/src/ss_model.xml   10     Active Shallow Crust 0           27           0            
========================= ====== ==================== =========== ============ =============

=============== =============
#TRT models     11           
#sources        3            
#ruptures       121368       
filtered_weight 148.425001621
=============== =============

Expected data transfer for the sources
--------------------------------------
=========================== =======
Number of tasks to generate 13     
Sent data                   2.57 MB
=========================== =======