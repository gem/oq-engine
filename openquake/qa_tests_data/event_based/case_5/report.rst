Germany_SHARE Combined Model event_based
========================================

num_sites = 100, sitecol = 5.13 KB

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             80         
investigation_time           30         
ses_per_logic_tree_path      1          
truncation_level             3.0000     
rupture_mesh_spacing         5.0000     
complex_fault_mesh_spacing   5.0000     
width_of_mfd_bin             0.1000     
area_source_discretization   10         
random_seed                  23         
master_seed                  0          
concurrent_tasks             16         
============================ ===========

Input files
-----------
======================= ==============================================================================
Name                    File                                                                          
======================= ==============================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                                          
sites                   `sites.csv <sites.csv>`_                                                      
source                  `as_model.xml <as_model.xml>`_                                                
source                  `fs_bg_source_model.xml <fs_bg_source_model.xml>`_                            
source                  `ss_model_final_250km_Buffer.xml <ss_model_final_250km_Buffer.xml>`_          
source_model_logic_tree `combined_logic-tree-source-model.xml <combined_logic-tree-source-model.xml>`_
======================= ==============================================================================

Composite source model
----------------------
========= ====== ================================================================================================ ================ ================
smlt_path weight source_model_file                                                                                gsim_logic_tree  num_realizations
========= ====== ================================================================================================ ================ ================
b1        0.50   `source_models/as_model.xml <source_models/as_model.xml>`_                                       trivial(1,0,0,0) 1/1             
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   simple(0,0,5,0)  5/5             
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ trivial(0,0,0,0) 0/0             
========= ====== ================================================================================================ ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================================================================== ================= ======================= =================
trt_id gsims                                                                                  distances         siteparams              ruptparams       
====== ====================================================================================== ================= ======================= =================
1      FaccioliEtAl2010                                                                       rrup              vs30                    rake mag         
4      AkkarBommer2010 Campbell2003SHARE CauzziFaccioli2008 ChiouYoungs2008 ToroEtAl2002SHARE rhypo rjb rx rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ====================================================================================== ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(6)
  1,FaccioliEtAl2010: ['<0,b1,@_@_@_b4_1,w=0.714285714286>']
  4,AkkarBommer2010: ['<1,b2,@_b2_1_@_@,w=0.0571428571429>']
  4,Campbell2003SHARE: ['<5,b2,@_b2_5_@_@,w=0.0571428571429>']
  4,CauzziFaccioli2008: ['<2,b2,@_b2_2_@_@,w=0.0571428571429>']
  4,ChiouYoungs2008: ['<3,b2,@_b2_3_@_@,w=0.0571428571429>']
  4,ToroEtAl2002SHARE: ['<4,b2,@_b2_4_@_@,w=0.0571428571429>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
1   b1        Volcanic             2           
4   b2        Stable Shallow Crust 3           
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
1           0           
4           1 2 3 4 5   
=========== ============

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 12       
Sent data                   5.12 MB  
Total received data         167.23 KB
Maximum received per task   34.6 KB  
=========================== =========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
4            327       AreaSource   1,544  5,145     0.0073      4.8013     26       
4            328       AreaSource   1,544  5,145     0.0172      5.0424     25       
4            329       AreaSource   1,544  5,145     0.0070      4.5968     23       
4            317       AreaSource   449    1         0.0024      0.0        12       
4            316       AreaSource   449    1         0.0025      0.0        12       
4            318       AreaSource   449    1         0.0024      0.0        12       
4            322       AreaSource   307    1         0.0014      0.0        10       
4            323       AreaSource   307    1         0.0014      0.0        8.5806   
4            264       AreaSource   85     1         0.0013      0.0        2.8195   
4            265       AreaSource   85     1         0.0013      0.0        2.4887   
4            263       AreaSource   85     1         0.0013      0.0        2.4473   
4            331       AreaSource   56     1         0.0014      0.0        2.1667   
4            332       AreaSource   56     1         0.0013      0.0        1.8074   
4            267       AreaSource   56     1         0.0011      0.0        1.7691   
4            330       AreaSource   56     1         0.0014      0.0        1.6993   
4            333       AreaSource   39     1         0.0014      0.0        1.5886   
4            334       AreaSource   39     1         0.0013      0.0        1.5318   
4            266       AreaSource   56     1         0.0012      0.0        1.4917   
4            249       AreaSource   30     1         0.0013      0.0        0.8507   
4            248       AreaSource   30     1         0.0013      0.0        0.8333   
============ ========= ============ ====== ========= =========== ========== =========