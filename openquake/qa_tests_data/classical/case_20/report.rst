Classical Hazard QA Test, Case 20
=================================

gem-tstation:/home/michele/ssd/calc_1007.hdf5 updated Thu Apr 28 15:40:59 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'classical'        
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           1.0                
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             1.0                
area_source_discretization   10.0               
random_seed                  106                
master_seed                  0                  
sites_per_tile               1000               
oqlite_version               '0.13.0-git93d6f64'
============================ ===================

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
========================= ====== ====================================== =============== ================
smlt_path                 weight source_model_file                      gsim_logic_tree num_realizations
========================= ====== ====================================== =============== ================
sm1_sg1_cog1_char_complex 0.070  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog1_char_plane   0.105  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog1_char_simple  0.175  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_complex 0.070  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_plane   0.105  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_simple  0.175  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_complex 0.030  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_plane   0.045  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_simple  0.075  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_complex 0.030  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_plane   0.045  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_simple  0.075  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========================= ====== ====================================== =============== ================

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

Informational data
------------------
======================================== ==============
count_eff_ruptures_max_received_per_task 2491          
count_eff_ruptures_num_tasks             90            
count_eff_ruptures_sent.monitor          201960        
count_eff_ruptures_sent.rlzs_assoc       1871550       
count_eff_ruptures_sent.sitecol          39330         
count_eff_ruptures_sent.siteidx          450           
count_eff_ruptures_sent.sources          3277138       
count_eff_ruptures_tot_received          224190        
hazard.input_weight                      1242.0        
hazard.n_imts                            1             
hazard.n_levels                          4.0           
hazard.n_realizations                    12            
hazard.n_sites                           1             
hazard.n_sources                         0             
hazard.output_weight                     48.0          
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ==================== ====== ========= =========== ========== =========
trt_model_id source_id source_class         weight split_num filter_time split_time calc_time
============ ========= ==================== ====== ========= =========== ========== =========
3            COMFLT1   ComplexFaultSource   62     62        0.002       1.005      0.0      
5            COMFLT1   ComplexFaultSource   62     62        0.002       0.793      0.0      
4            COMFLT1   ComplexFaultSource   62     62        0.002       0.772      0.0      
9            COMFLT1   ComplexFaultSource   62     62        0.002       0.771      0.0      
11           COMFLT1   ComplexFaultSource   62     62        0.002       0.733      0.0      
10           COMFLT1   ComplexFaultSource   62     62        0.002       0.728      0.0      
3            SFLT1     SimpleFaultSource    56     56        0.003       0.085      0.0      
0            SFLT1     SimpleFaultSource    56     56        0.003       0.050      0.0      
1            SFLT1     SimpleFaultSource    56     56        0.004       0.045      0.0      
6            SFLT1     SimpleFaultSource    58     58        0.003       0.046      0.0      
7            SFLT1     SimpleFaultSource    58     58        0.003       0.046      0.0      
4            SFLT1     SimpleFaultSource    56     56        0.003       0.046      0.0      
8            SFLT1     SimpleFaultSource    58     58        0.003       0.046      0.0      
2            SFLT1     SimpleFaultSource    56     56        0.003       0.045      0.0      
5            SFLT1     SimpleFaultSource    56     56        0.003       0.045      0.0      
9            SFLT1     SimpleFaultSource    58     58        0.003       0.045      0.0      
11           SFLT1     SimpleFaultSource    58     58        0.003       0.044      0.0      
10           SFLT1     SimpleFaultSource    58     58        0.003       0.043      0.0      
0            CHAR1     CharacteristicFaultS 1.000  1         0.003       0.0        0.0      
4            CHAR1     CharacteristicFaultS 1.000  1         0.003       0.0        0.0      
============ ========= ==================== ====== ========= =========== ========== =========

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               6.413     0.0       1     
splitting sources              5.390     0.0       18    
reading composite source model 2.059     0.0       1     
filtering sources              0.094     0.0       36    
total count_eff_ruptures       0.025     0.0       90    
store source_info              0.007     0.0       1     
aggregate curves               0.002     0.0       90    
reading site collection        4.482E-05 0.0       1     
============================== ========= ========= ======