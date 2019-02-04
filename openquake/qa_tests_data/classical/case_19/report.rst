SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     3,058,858,863      
date           2019-02-03T09:40:31
engine_version 3.4.0-gite8c42e513a
============== ===================

num_sites = 1, num_levels = 78

Parameters
----------
=============================== ===========================================
calculation_mode                'preclassical'                             
number_of_logic_tree_samples    0                                          
maximum_distance                {'default': [(6, 100), (7, 150), (9, 200)]}
investigation_time              50.0                                       
ses_per_logic_tree_path         1                                          
truncation_level                3.0                                        
rupture_mesh_spacing            5.0                                        
complex_fault_mesh_spacing      5.0                                        
width_of_mfd_bin                0.2                                        
area_source_discretization      10.0                                       
ground_motion_correlation_model None                                       
minimum_intensity               {}                                         
random_seed                     23                                         
master_seed                     0                                          
ses_seed                        42                                         
=============================== ===========================================

Input files
-----------
======================= ==========================================================================
Name                    File                                                                      
======================= ==========================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_            
job_ini                 `job.ini <job.ini>`_                                                      
source_model_logic_tree `simple_source_model_logic_tree.xml <simple_source_model_logic_tree.xml>`_
======================= ==========================================================================

Composite source model
----------------------
========= ======= ====================== ================
smlt_path weight  gsim_logic_tree        num_realizations
========= ======= ====================== ================
b1        1.00000 complex(0,5,2,4,4,1,0) 160             
========= ======= ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= =================
grp_id gsims                                                                                            distances         siteparams              ruptparams       
====== ================================================================================================ ================= ======================= =================
0      AtkinsonBoore2003SInter() LinLee2008SInter() YoungsEtAl1997SInter() ZhaoEtAl2006SInter()         rhypo rrup        vs30                    hypo_depth mag   
1      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake         
2      Campbell2003SHARE() ToroEtAl2002SHARE()                                                          rjb rrup                                  mag rake         
3      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
4      AtkinsonBoore2003SSlab() LinLee2008SSlab() YoungsEtAl1997SSlab() ZhaoEtAl2006SSlab()             rhypo rrup        vs30                    hypo_depth mag   
====== ================================================================================================ ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=16, rlzs=160)
  0,AtkinsonBoore2003SInter(): ['40 realizations']
  0,LinLee2008SInter(): ['40 realizations']
  0,YoungsEtAl1997SInter(): ['40 realizations']
  0,ZhaoEtAl2006SInter(): ['40 realizations']
  1,FaccioliEtAl2010(): ['160 realizations']
  2,Campbell2003SHARE(): ['80 realizations']
  2,ToroEtAl2002SHARE(): ['80 realizations']
  3,AkkarBommer2010(): ['32 realizations']
  3,Campbell2003SHARE(): ['32 realizations']
  3,CauzziFaccioli2008(): ['32 realizations']
  3,ChiouYoungs2008(): ['32 realizations']
  3,ToroEtAl2002SHARE(): ['32 realizations']
  4,AtkinsonBoore2003SSlab(): ['40 realizations']
  4,LinLee2008SSlab(): ['40 realizations']
  4,YoungsEtAl1997SSlab(): ['40 realizations']
  4,ZhaoEtAl2006SSlab(): ['40 realizations']>

Number of ruptures per tectonic region type
-------------------------------------------
============================ ====== ==================== ============ ============
source_model                 grp_id trt                  eff_ruptures tot_ruptures
============================ ====== ==================== ============ ============
simple_area_source_model.xml 0      Subduction Interface 42,624       42,624      
simple_area_source_model.xml 1      Volcanic             210          210         
simple_area_source_model.xml 2      Shield               96,804       96,804      
simple_area_source_model.xml 3      Stable Shallow Crust 81,154       81,154      
simple_area_source_model.xml 4      Subduction Inslab    93,219       93,219      
============================ ====== ==================== ============ ============

============= =======
#TRT models   5      
#eff_ruptures 314,011
#tot_ruptures 314,011
#tot_weight   197,635
============= =======

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
4      s72       A    711   739   17,871       0.0       0.0        1.00000   0         1,787  
4      s70       A    683   711   17,871       0.0       0.0        1.00000   0         1,787  
4      s46       A    657   683   7,770        0.0       0.0        1.00000   0         777    
4      s40       A    631   657   12,327       0.0       0.0        1.00000   0         1,233  
4      s35       A    605   631   12,327       0.0       0.0        1.00000   0         1,233  
4      s34       A    579   605   12,327       0.0       0.0        1.00000   0         1,233  
4      s13       A    553   579   12,726       0.0       0.0        1.00000   0         1,273  
3      scr304    A    543   553   574          0.0       0.0        1.00000   0         57     
3      scr301    A    506   543   17,268       0.0       0.0        1.00000   0         1,727  
3      scr299    A    496   506   1,572        0.0       0.0        1.00000   0         157    
3      scr293    A    369   496   61,740       0.0       0.0        1.00000   0         6,174  
2      sh6       A    362   369   12,900       0.0       0.0        1.00000   0         1,290  
2      sh14      A    350   362   41,952       0.0       0.0        1.00000   0         4,195  
2      sh13      A    338   350   41,952       0.0       0.0        1.00000   0         4,195  
1      v4        A    327   338   168          0.0       0.0        1.00000   0         16     
1      v1        A    323   327   42           0.0       0.0        1.00000   0         4.20000
0      i20       C    217   323   9,241        0.0       0.0        1.00000   0         36,964 
0      i17       C    0     217   33,383       0.0       0.0        1.00000   0         133,532
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       16    
C    0.0       2     
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 5.23580 NaN    5.23580 5.23580 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=313 B fnames=119 B 45.04 KB
================== ============================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 5.23580  5.33984   1     
======================== ======== ========= ======