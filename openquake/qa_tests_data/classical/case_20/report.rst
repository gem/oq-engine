Classical Hazard QA Test, Case 20
=================================

num_sites = 1, sitecol = 684 B

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200      
investigation_time           1.000    
ses_per_logic_tree_path      1        
truncation_level             3.000    
rupture_mesh_spacing         2.000    
complex_fault_mesh_spacing   2.000    
width_of_mfd_bin             1.000    
area_source_discretization   10       
random_seed                  106      
master_seed                  0        
concurrent_tasks             16       
sites_per_tile               1000     
============================ =========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========================= ======= ====================================== =============== ================
smlt_path                 weight  source_model_file                      gsim_logic_tree num_realizations
========================= ======= ====================================== =============== ================
sm1_sg1_cog1_char_complex 0.07000 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog1_char_plane   0.10500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog1_char_simple  0.17500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_complex 0.07000 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_plane   0.10500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_simple  0.17500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_complex 0.03000 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_plane   0.04500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_simple  0.07500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_complex 0.03000 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_plane   0.04500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_simple  0.07500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========================= ======= ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============== ========= ========== ==========
trt_id gsims          distances siteparams ruptparams
====== ============== ========= ========== ==========
0      SadighEtAl1997 rrup      vs30       rake mag  
1      SadighEtAl1997 rrup      vs30       rake mag  
2      SadighEtAl1997 rrup      vs30       rake mag  
3      SadighEtAl1997 rrup      vs30       rake mag  
4      SadighEtAl1997 rrup      vs30       rake mag  
5      SadighEtAl1997 rrup      vs30       rake mag  
6      SadighEtAl1997 rrup      vs30       rake mag  
7      SadighEtAl1997 rrup      vs30       rake mag  
8      SadighEtAl1997 rrup      vs30       rake mag  
9      SadighEtAl1997 rrup      vs30       rake mag  
10     SadighEtAl1997 rrup      vs30       rake mag  
11     SadighEtAl1997 rrup      vs30       rake mag  
====== ============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=12, rlzs=12)
  0,SadighEtAl1997: ['<0,sm1_sg1_cog1_char_complex,Sad1997,w=0.07>']
  1,SadighEtAl1997: ['<1,sm1_sg1_cog1_char_plane,Sad1997,w=0.105>']
  2,SadighEtAl1997: ['<2,sm1_sg1_cog1_char_simple,Sad1997,w=0.175>']
  3,SadighEtAl1997: ['<3,sm1_sg1_cog2_char_complex,Sad1997,w=0.07>']
  4,SadighEtAl1997: ['<4,sm1_sg1_cog2_char_plane,Sad1997,w=0.105>']
  5,SadighEtAl1997: ['<5,sm1_sg1_cog2_char_simple,Sad1997,w=0.175>']
  6,SadighEtAl1997: ['<6,sm1_sg2_cog1_char_complex,Sad1997,w=0.03>']
  7,SadighEtAl1997: ['<7,sm1_sg2_cog1_char_plane,Sad1997,w=0.045>']
  8,SadighEtAl1997: ['<8,sm1_sg2_cog1_char_simple,Sad1997,w=0.075>']
  9,SadighEtAl1997: ['<9,sm1_sg2_cog2_char_complex,Sad1997,w=0.03>']
  10,SadighEtAl1997: ['<10,sm1_sg2_cog2_char_plane,Sad1997,w=0.045>']
  11,SadighEtAl1997: ['<11,sm1_sg2_cog2_char_simple,Sad1997,w=0.075>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 3           86           86    
source_model.xml 1      Active Shallow Crust 3           86           86    
source_model.xml 2      Active Shallow Crust 3           86           86    
source_model.xml 3      Active Shallow Crust 3           119          119   
source_model.xml 4      Active Shallow Crust 3           119          119   
source_model.xml 5      Active Shallow Crust 3           119          119   
source_model.xml 6      Active Shallow Crust 3           88           88    
source_model.xml 7      Active Shallow Crust 3           88           88    
source_model.xml 8      Active Shallow Crust 3           88           88    
source_model.xml 9      Active Shallow Crust 3           121          121   
source_model.xml 10     Active Shallow Crust 3           121          121   
source_model.xml 11     Active Shallow Crust 3           121          121   
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     12   
#sources        36   
#eff_ruptures   1,242
filtered_weight 1,242
=============== =====

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 24       
Sent data                   631.44 KB
=========================== =========

Slowest sources
---------------
============ ========= ==================== ====== ========= =========== ========== =========
trt_model_id source_id source_class         weight split_num filter_time split_time calc_time
============ ========= ==================== ====== ========= =========== ========== =========
7            SFLT1     SimpleFaultSource    58     1         0.002       0.0        0.0      
0            SFLT1     SimpleFaultSource    56     1         0.002       0.0        0.0      
3            SFLT1     SimpleFaultSource    56     1         0.002       0.0        0.0      
4            SFLT1     SimpleFaultSource    56     1         0.002       0.0        0.0      
0            CHAR1     CharacteristicFaultS 1.000  1         0.002       0.0        0.0      
11           SFLT1     SimpleFaultSource    58     1         0.002       0.0        0.0      
1            SFLT1     SimpleFaultSource    56     1         0.002       0.0        0.0      
10           SFLT1     SimpleFaultSource    58     1         0.002       0.0        0.0      
5            SFLT1     SimpleFaultSource    56     1         0.002       0.0        0.0      
2            SFLT1     SimpleFaultSource    56     1         0.002       0.0        0.0      
8            SFLT1     SimpleFaultSource    58     1         0.002       0.0        0.0      
9            SFLT1     SimpleFaultSource    58     1         0.002       0.0        0.0      
6            SFLT1     SimpleFaultSource    58     1         0.002       0.0        0.0      
3            CHAR1     CharacteristicFaultS 1.000  1         0.002       0.0        0.0      
10           CHAR1     CharacteristicFaultS 1.000  1         0.002       0.0        0.0      
1            CHAR1     CharacteristicFaultS 1.000  1         0.002       0.0        0.0      
4            CHAR1     CharacteristicFaultS 1.000  1         0.002       0.0        0.0      
7            CHAR1     CharacteristicFaultS 1.000  1         0.002       0.0        0.0      
8            CHAR1     CharacteristicFaultS 1.000  1         0.002       0.0        0.0      
3            COMFLT1   ComplexFaultSource   62     1         0.002       0.0        0.0      
============ ========= ==================== ====== ========= =========== ========== =========