Classical Hazard QA Test, Case 20
=================================

num_sites = 1

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         2.0      
complex_fault_mesh_spacing   2.0      
width_of_mfd_bin             1.0      
area_source_discretization   10.0     
random_seed                  106      
master_seed                  0        
concurrent_tasks             32       
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
========================= ======= ====================================== =============== ================ ===========
smlt_path                 weight  source_model_file                      gsim_logic_tree num_realizations num_sources
========================= ======= ====================================== =============== ================ ===========
sm1_sg1_cog1_char_complex 0.07000 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              86         
sm1_sg1_cog1_char_plane   0.10500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              86         
sm1_sg1_cog1_char_simple  0.17500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              86         
sm1_sg1_cog2_char_complex 0.07000 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              119        
sm1_sg1_cog2_char_plane   0.10500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              119        
sm1_sg1_cog2_char_simple  0.17500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              119        
sm1_sg2_cog1_char_complex 0.03000 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              88         
sm1_sg2_cog1_char_plane   0.04500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              88         
sm1_sg2_cog1_char_simple  0.07500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              88         
sm1_sg2_cog2_char_complex 0.03000 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              121        
sm1_sg2_cog2_char_plane   0.04500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              121        
sm1_sg2_cog2_char_simple  0.07500 `source_model.xml <source_model.xml>`_ trivial(1)      1/1              121        
========================= ======= ====================================== =============== ================ ===========

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

  <RlzsAssoc(12)
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
=========== ====
#TRT models 12  
#sources    1242
#ruptures   1242
=========== ====

================ ====== ==================== =========== ============
source_model     trt_id trt                  num_sources num_ruptures
================ ====== ==================== =========== ============
source_model.xml 0      Active Shallow Crust 86          86          
source_model.xml 1      Active Shallow Crust 86          86          
source_model.xml 2      Active Shallow Crust 86          86          
source_model.xml 3      Active Shallow Crust 119         119         
source_model.xml 4      Active Shallow Crust 119         119         
source_model.xml 5      Active Shallow Crust 119         119         
source_model.xml 6      Active Shallow Crust 88          88          
source_model.xml 7      Active Shallow Crust 88          88          
source_model.xml 8      Active Shallow Crust 88          88          
source_model.xml 9      Active Shallow Crust 121         121         
source_model.xml 10     Active Shallow Crust 121         121         
source_model.xml 11     Active Shallow Crust 121         121         
================ ====== ==================== =========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        42     
Estimated sources to send          3.57 MB
Estimated hazard curves to receive 1 KB   
================================== =======