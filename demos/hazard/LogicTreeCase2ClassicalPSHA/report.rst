Classical PSHA with non-trivial logic tree (1 source model + absolute uncertainties on G-R a and b values and maximum magnitude and 2 GMPEs per tectonic region type)
=====================================================================================================================================================================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'classical'        
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             0.1                
area_source_discretization   5.0                
random_seed                  23                 
master_seed                  0                  
concurrent_tasks             40                 
sites_per_tile               1000               
oqlite_version               '0.13.0-gite77b1a1'
============================ ===================

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
=================== ====== ====================================== =============== ================
smlt_path           weight source_model_file                      gsim_logic_tree num_realizations
=================== ====== ====================================== =============== ================
b11_b21_b31_b41_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b31_b41_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b31_b41_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b31_b42_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b31_b42_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b31_b42_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b31_b43_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b31_b43_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b31_b43_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b32_b41_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b32_b41_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b32_b41_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b32_b42_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b32_b42_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b32_b42_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b32_b43_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b32_b43_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b32_b43_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b33_b41_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b33_b41_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b33_b41_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b33_b42_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b33_b42_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b33_b42_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b33_b43_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b33_b43_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b33_b43_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b31_b41_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b31_b41_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b31_b41_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b31_b42_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b31_b42_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b31_b42_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b31_b43_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b31_b43_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b31_b43_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b32_b41_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b32_b41_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b32_b41_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b32_b42_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b32_b42_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b32_b42_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b32_b43_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b32_b43_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b32_b43_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b33_b41_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b33_b41_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b33_b41_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b33_b42_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b33_b42_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b33_b42_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b33_b43_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b33_b43_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b33_b43_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b31_b41_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b31_b41_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b31_b41_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b31_b42_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b31_b42_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b31_b42_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b31_b43_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b31_b43_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b31_b43_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b32_b41_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b32_b41_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b32_b41_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b32_b42_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b32_b42_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b32_b42_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b32_b43_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b32_b43_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b32_b43_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b33_b41_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b33_b41_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b33_b41_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b33_b42_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b33_b42_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b33_b42_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b33_b43_b51 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b33_b43_b52 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b33_b43_b53 0.012  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
=================== ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================= =========== ======================= =================
trt_id gsims                             distances   siteparams              ruptparams       
====== ================================= =========== ======================= =================
0      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
1      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
2      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
3      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
4      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
5      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
6      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
7      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
8      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
9      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
10     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
11     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
12     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
13     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
14     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
15     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
16     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
17     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
18     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
19     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
20     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
21     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
22     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
23     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
24     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
25     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
26     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
27     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
28     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
29     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
30     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
31     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
32     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
33     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
34     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
35     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
36     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
37     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
38     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
39     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
40     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
41     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
42     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
43     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
44     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
45     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
46     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
47     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
48     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
49     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
50     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
51     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
52     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
53     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
54     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
55     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
56     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
57     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
58     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
59     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
60     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
61     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
62     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
63     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
64     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
65     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
66     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
67     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
68     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
69     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
70     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
71     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
72     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
73     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
74     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
75     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
76     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
77     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
78     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
79     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
80     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
81     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
82     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
83     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
84     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
85     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
86     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
87     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
88     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
89     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
90     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
91     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
92     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
93     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
94     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
95     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
96     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
97     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
98     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
99     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
100    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
101    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
102    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
103    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
104    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
105    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
106    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
107    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
108    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
109    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
110    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
111    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
112    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
113    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
114    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
115    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
116    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
117    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
118    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
119    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
120    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
121    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
122    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
123    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
124    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
125    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
126    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
127    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
128    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
129    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
130    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
131    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
132    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
133    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
134    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
135    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
136    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
137    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
138    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
139    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
140    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
141    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
142    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
143    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
144    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
145    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
146    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
147    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
148    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
149    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
150    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
151    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
152    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
153    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
154    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
155    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
156    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
157    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
158    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
159    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
160    BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
161    Campbell2003 ToroEtAl2002         rjb rrup                            mag              
====== ================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=324, rlzs=324)
  0,BooreAtkinson2008: ['<0,b11_b21_b31_b41_b51,b11_b21,w=0.00307409258025>', '<1,b11_b21_b31_b41_b51,b11_b22,w=0.00307409258025>']
  0,ChiouYoungs2008: ['<2,b11_b21_b31_b41_b51,b12_b21,w=0.00307409258025>', '<3,b11_b21_b31_b41_b51,b12_b22,w=0.00307409258025>']
  1,Campbell2003: ['<1,b11_b21_b31_b41_b51,b11_b22,w=0.00307409258025>', '<3,b11_b21_b31_b41_b51,b12_b22,w=0.00307409258025>']
  1,ToroEtAl2002: ['<0,b11_b21_b31_b41_b51,b11_b21,w=0.00307409258025>', '<2,b11_b21_b31_b41_b51,b12_b21,w=0.00307409258025>']
  2,BooreAtkinson2008: ['<4,b11_b21_b31_b41_b52,b11_b21,w=0.00307409258025>', '<5,b11_b21_b31_b41_b52,b11_b22,w=0.00307409258025>']
  2,ChiouYoungs2008: ['<6,b11_b21_b31_b41_b52,b12_b21,w=0.00307409258025>', '<7,b11_b21_b31_b41_b52,b12_b22,w=0.00307409258025>']
  3,Campbell2003: ['<5,b11_b21_b31_b41_b52,b11_b22,w=0.00307409258025>', '<7,b11_b21_b31_b41_b52,b12_b22,w=0.00307409258025>']
  3,ToroEtAl2002: ['<4,b11_b21_b31_b41_b52,b11_b21,w=0.00307409258025>', '<6,b11_b21_b31_b41_b52,b12_b21,w=0.00307409258025>']
  4,BooreAtkinson2008: ['<8,b11_b21_b31_b41_b53,b11_b21,w=0.0030833240895>', '<9,b11_b21_b31_b41_b53,b11_b22,w=0.0030833240895>']
  4,ChiouYoungs2008: ['<10,b11_b21_b31_b41_b53,b12_b21,w=0.0030833240895>', '<11,b11_b21_b31_b41_b53,b12_b22,w=0.0030833240895>']
  5,Campbell2003: ['<9,b11_b21_b31_b41_b53,b11_b22,w=0.0030833240895>', '<11,b11_b21_b31_b41_b53,b12_b22,w=0.0030833240895>']
  5,ToroEtAl2002: ['<8,b11_b21_b31_b41_b53,b11_b21,w=0.0030833240895>', '<10,b11_b21_b31_b41_b53,b12_b21,w=0.0030833240895>']
  6,BooreAtkinson2008: ['<12,b11_b21_b31_b42_b51,b11_b21,w=0.00307409258025>', '<13,b11_b21_b31_b42_b51,b11_b22,w=0.00307409258025>']
  6,ChiouYoungs2008: ['<14,b11_b21_b31_b42_b51,b12_b21,w=0.00307409258025>', '<15,b11_b21_b31_b42_b51,b12_b22,w=0.00307409258025>']
  7,Campbell2003: ['<13,b11_b21_b31_b42_b51,b11_b22,w=0.00307409258025>', '<15,b11_b21_b31_b42_b51,b12_b22,w=0.00307409258025>']
  7,ToroEtAl2002: ['<12,b11_b21_b31_b42_b51,b11_b21,w=0.00307409258025>', '<14,b11_b21_b31_b42_b51,b12_b21,w=0.00307409258025>']
  8,BooreAtkinson2008: ['<16,b11_b21_b31_b42_b52,b11_b21,w=0.00307409258025>', '<17,b11_b21_b31_b42_b52,b11_b22,w=0.00307409258025>']
  8,ChiouYoungs2008: ['<18,b11_b21_b31_b42_b52,b12_b21,w=0.00307409258025>', '<19,b11_b21_b31_b42_b52,b12_b22,w=0.00307409258025>']
  9,Campbell2003: ['<17,b11_b21_b31_b42_b52,b11_b22,w=0.00307409258025>', '<19,b11_b21_b31_b42_b52,b12_b22,w=0.00307409258025>']
  9,ToroEtAl2002: ['<16,b11_b21_b31_b42_b52,b11_b21,w=0.00307409258025>', '<18,b11_b21_b31_b42_b52,b12_b21,w=0.00307409258025>']
  10,BooreAtkinson2008: ['<20,b11_b21_b31_b42_b53,b11_b21,w=0.0030833240895>', '<21,b11_b21_b31_b42_b53,b11_b22,w=0.0030833240895>']
  10,ChiouYoungs2008: ['<22,b11_b21_b31_b42_b53,b12_b21,w=0.0030833240895>', '<23,b11_b21_b31_b42_b53,b12_b22,w=0.0030833240895>']
  11,Campbell2003: ['<21,b11_b21_b31_b42_b53,b11_b22,w=0.0030833240895>', '<23,b11_b21_b31_b42_b53,b12_b22,w=0.0030833240895>']
  11,ToroEtAl2002: ['<20,b11_b21_b31_b42_b53,b11_b21,w=0.0030833240895>', '<22,b11_b21_b31_b42_b53,b12_b21,w=0.0030833240895>']
  12,BooreAtkinson2008: ['<24,b11_b21_b31_b43_b51,b11_b21,w=0.0030833240895>', '<25,b11_b21_b31_b43_b51,b11_b22,w=0.0030833240895>']
  12,ChiouYoungs2008: ['<26,b11_b21_b31_b43_b51,b12_b21,w=0.0030833240895>', '<27,b11_b21_b31_b43_b51,b12_b22,w=0.0030833240895>']
  13,Campbell2003: ['<25,b11_b21_b31_b43_b51,b11_b22,w=0.0030833240895>', '<27,b11_b21_b31_b43_b51,b12_b22,w=0.0030833240895>']
  13,ToroEtAl2002: ['<24,b11_b21_b31_b43_b51,b11_b21,w=0.0030833240895>', '<26,b11_b21_b31_b43_b51,b12_b21,w=0.0030833240895>']
  14,BooreAtkinson2008: ['<28,b11_b21_b31_b43_b52,b11_b21,w=0.0030833240895>', '<29,b11_b21_b31_b43_b52,b11_b22,w=0.0030833240895>']
  14,ChiouYoungs2008: ['<30,b11_b21_b31_b43_b52,b12_b21,w=0.0030833240895>', '<31,b11_b21_b31_b43_b52,b12_b22,w=0.0030833240895>']
  15,Campbell2003: ['<29,b11_b21_b31_b43_b52,b11_b22,w=0.0030833240895>', '<31,b11_b21_b31_b43_b52,b12_b22,w=0.0030833240895>']
  15,ToroEtAl2002: ['<28,b11_b21_b31_b43_b52,b11_b21,w=0.0030833240895>', '<30,b11_b21_b31_b43_b52,b12_b21,w=0.0030833240895>']
  16,BooreAtkinson2008: ['<32,b11_b21_b31_b43_b53,b11_b21,w=0.003092583321>', '<33,b11_b21_b31_b43_b53,b11_b22,w=0.003092583321>']
  16,ChiouYoungs2008: ['<34,b11_b21_b31_b43_b53,b12_b21,w=0.003092583321>', '<35,b11_b21_b31_b43_b53,b12_b22,w=0.003092583321>']
  17,Campbell2003: ['<33,b11_b21_b31_b43_b53,b11_b22,w=0.003092583321>', '<35,b11_b21_b31_b43_b53,b12_b22,w=0.003092583321>']
  17,ToroEtAl2002: ['<32,b11_b21_b31_b43_b53,b11_b21,w=0.003092583321>', '<34,b11_b21_b31_b43_b53,b12_b21,w=0.003092583321>']
  18,BooreAtkinson2008: ['<36,b11_b21_b32_b41_b51,b11_b21,w=0.00307409258025>', '<37,b11_b21_b32_b41_b51,b11_b22,w=0.00307409258025>']
  18,ChiouYoungs2008: ['<38,b11_b21_b32_b41_b51,b12_b21,w=0.00307409258025>', '<39,b11_b21_b32_b41_b51,b12_b22,w=0.00307409258025>']
  19,Campbell2003: ['<37,b11_b21_b32_b41_b51,b11_b22,w=0.00307409258025>', '<39,b11_b21_b32_b41_b51,b12_b22,w=0.00307409258025>']
  19,ToroEtAl2002: ['<36,b11_b21_b32_b41_b51,b11_b21,w=0.00307409258025>', '<38,b11_b21_b32_b41_b51,b12_b21,w=0.00307409258025>']
  20,BooreAtkinson2008: ['<40,b11_b21_b32_b41_b52,b11_b21,w=0.00307409258025>', '<41,b11_b21_b32_b41_b52,b11_b22,w=0.00307409258025>']
  20,ChiouYoungs2008: ['<42,b11_b21_b32_b41_b52,b12_b21,w=0.00307409258025>', '<43,b11_b21_b32_b41_b52,b12_b22,w=0.00307409258025>']
  21,Campbell2003: ['<41,b11_b21_b32_b41_b52,b11_b22,w=0.00307409258025>', '<43,b11_b21_b32_b41_b52,b12_b22,w=0.00307409258025>']
  21,ToroEtAl2002: ['<40,b11_b21_b32_b41_b52,b11_b21,w=0.00307409258025>', '<42,b11_b21_b32_b41_b52,b12_b21,w=0.00307409258025>']
  22,BooreAtkinson2008: ['<44,b11_b21_b32_b41_b53,b11_b21,w=0.0030833240895>', '<45,b11_b21_b32_b41_b53,b11_b22,w=0.0030833240895>']
  22,ChiouYoungs2008: ['<46,b11_b21_b32_b41_b53,b12_b21,w=0.0030833240895>', '<47,b11_b21_b32_b41_b53,b12_b22,w=0.0030833240895>']
  23,Campbell2003: ['<45,b11_b21_b32_b41_b53,b11_b22,w=0.0030833240895>', '<47,b11_b21_b32_b41_b53,b12_b22,w=0.0030833240895>']
  23,ToroEtAl2002: ['<44,b11_b21_b32_b41_b53,b11_b21,w=0.0030833240895>', '<46,b11_b21_b32_b41_b53,b12_b21,w=0.0030833240895>']
  24,BooreAtkinson2008: ['<48,b11_b21_b32_b42_b51,b11_b21,w=0.00307409258025>', '<49,b11_b21_b32_b42_b51,b11_b22,w=0.00307409258025>']
  24,ChiouYoungs2008: ['<50,b11_b21_b32_b42_b51,b12_b21,w=0.00307409258025>', '<51,b11_b21_b32_b42_b51,b12_b22,w=0.00307409258025>']
  25,Campbell2003: ['<49,b11_b21_b32_b42_b51,b11_b22,w=0.00307409258025>', '<51,b11_b21_b32_b42_b51,b12_b22,w=0.00307409258025>']
  25,ToroEtAl2002: ['<48,b11_b21_b32_b42_b51,b11_b21,w=0.00307409258025>', '<50,b11_b21_b32_b42_b51,b12_b21,w=0.00307409258025>']
  26,BooreAtkinson2008: ['<52,b11_b21_b32_b42_b52,b11_b21,w=0.00307409258025>', '<53,b11_b21_b32_b42_b52,b11_b22,w=0.00307409258025>']
  26,ChiouYoungs2008: ['<54,b11_b21_b32_b42_b52,b12_b21,w=0.00307409258025>', '<55,b11_b21_b32_b42_b52,b12_b22,w=0.00307409258025>']
  27,Campbell2003: ['<53,b11_b21_b32_b42_b52,b11_b22,w=0.00307409258025>', '<55,b11_b21_b32_b42_b52,b12_b22,w=0.00307409258025>']
  27,ToroEtAl2002: ['<52,b11_b21_b32_b42_b52,b11_b21,w=0.00307409258025>', '<54,b11_b21_b32_b42_b52,b12_b21,w=0.00307409258025>']
  28,BooreAtkinson2008: ['<56,b11_b21_b32_b42_b53,b11_b21,w=0.0030833240895>', '<57,b11_b21_b32_b42_b53,b11_b22,w=0.0030833240895>']
  28,ChiouYoungs2008: ['<58,b11_b21_b32_b42_b53,b12_b21,w=0.0030833240895>', '<59,b11_b21_b32_b42_b53,b12_b22,w=0.0030833240895>']
  29,Campbell2003: ['<57,b11_b21_b32_b42_b53,b11_b22,w=0.0030833240895>', '<59,b11_b21_b32_b42_b53,b12_b22,w=0.0030833240895>']
  29,ToroEtAl2002: ['<56,b11_b21_b32_b42_b53,b11_b21,w=0.0030833240895>', '<58,b11_b21_b32_b42_b53,b12_b21,w=0.0030833240895>']
  30,BooreAtkinson2008: ['<60,b11_b21_b32_b43_b51,b11_b21,w=0.0030833240895>', '<61,b11_b21_b32_b43_b51,b11_b22,w=0.0030833240895>']
  30,ChiouYoungs2008: ['<62,b11_b21_b32_b43_b51,b12_b21,w=0.0030833240895>', '<63,b11_b21_b32_b43_b51,b12_b22,w=0.0030833240895>']
  31,Campbell2003: ['<61,b11_b21_b32_b43_b51,b11_b22,w=0.0030833240895>', '<63,b11_b21_b32_b43_b51,b12_b22,w=0.0030833240895>']
  31,ToroEtAl2002: ['<60,b11_b21_b32_b43_b51,b11_b21,w=0.0030833240895>', '<62,b11_b21_b32_b43_b51,b12_b21,w=0.0030833240895>']
  32,BooreAtkinson2008: ['<64,b11_b21_b32_b43_b52,b11_b21,w=0.0030833240895>', '<65,b11_b21_b32_b43_b52,b11_b22,w=0.0030833240895>']
  32,ChiouYoungs2008: ['<66,b11_b21_b32_b43_b52,b12_b21,w=0.0030833240895>', '<67,b11_b21_b32_b43_b52,b12_b22,w=0.0030833240895>']
  33,Campbell2003: ['<65,b11_b21_b32_b43_b52,b11_b22,w=0.0030833240895>', '<67,b11_b21_b32_b43_b52,b12_b22,w=0.0030833240895>']
  33,ToroEtAl2002: ['<64,b11_b21_b32_b43_b52,b11_b21,w=0.0030833240895>', '<66,b11_b21_b32_b43_b52,b12_b21,w=0.0030833240895>']
  34,BooreAtkinson2008: ['<68,b11_b21_b32_b43_b53,b11_b21,w=0.003092583321>', '<69,b11_b21_b32_b43_b53,b11_b22,w=0.003092583321>']
  34,ChiouYoungs2008: ['<70,b11_b21_b32_b43_b53,b12_b21,w=0.003092583321>', '<71,b11_b21_b32_b43_b53,b12_b22,w=0.003092583321>']
  35,Campbell2003: ['<69,b11_b21_b32_b43_b53,b11_b22,w=0.003092583321>', '<71,b11_b21_b32_b43_b53,b12_b22,w=0.003092583321>']
  35,ToroEtAl2002: ['<68,b11_b21_b32_b43_b53,b11_b21,w=0.003092583321>', '<70,b11_b21_b32_b43_b53,b12_b21,w=0.003092583321>']
  36,BooreAtkinson2008: ['<72,b11_b21_b33_b41_b51,b11_b21,w=0.0030833240895>', '<73,b11_b21_b33_b41_b51,b11_b22,w=0.0030833240895>']
  36,ChiouYoungs2008: ['<74,b11_b21_b33_b41_b51,b12_b21,w=0.0030833240895>', '<75,b11_b21_b33_b41_b51,b12_b22,w=0.0030833240895>']
  37,Campbell2003: ['<73,b11_b21_b33_b41_b51,b11_b22,w=0.0030833240895>', '<75,b11_b21_b33_b41_b51,b12_b22,w=0.0030833240895>']
  37,ToroEtAl2002: ['<72,b11_b21_b33_b41_b51,b11_b21,w=0.0030833240895>', '<74,b11_b21_b33_b41_b51,b12_b21,w=0.0030833240895>']
  38,BooreAtkinson2008: ['<76,b11_b21_b33_b41_b52,b11_b21,w=0.0030833240895>', '<77,b11_b21_b33_b41_b52,b11_b22,w=0.0030833240895>']
  38,ChiouYoungs2008: ['<78,b11_b21_b33_b41_b52,b12_b21,w=0.0030833240895>', '<79,b11_b21_b33_b41_b52,b12_b22,w=0.0030833240895>']
  39,Campbell2003: ['<77,b11_b21_b33_b41_b52,b11_b22,w=0.0030833240895>', '<79,b11_b21_b33_b41_b52,b12_b22,w=0.0030833240895>']
  39,ToroEtAl2002: ['<76,b11_b21_b33_b41_b52,b11_b21,w=0.0030833240895>', '<78,b11_b21_b33_b41_b52,b12_b21,w=0.0030833240895>']
  40,BooreAtkinson2008: ['<80,b11_b21_b33_b41_b53,b11_b21,w=0.003092583321>', '<81,b11_b21_b33_b41_b53,b11_b22,w=0.003092583321>']
  40,ChiouYoungs2008: ['<82,b11_b21_b33_b41_b53,b12_b21,w=0.003092583321>', '<83,b11_b21_b33_b41_b53,b12_b22,w=0.003092583321>']
  41,Campbell2003: ['<81,b11_b21_b33_b41_b53,b11_b22,w=0.003092583321>', '<83,b11_b21_b33_b41_b53,b12_b22,w=0.003092583321>']
  41,ToroEtAl2002: ['<80,b11_b21_b33_b41_b53,b11_b21,w=0.003092583321>', '<82,b11_b21_b33_b41_b53,b12_b21,w=0.003092583321>']
  42,BooreAtkinson2008: ['<84,b11_b21_b33_b42_b51,b11_b21,w=0.0030833240895>', '<85,b11_b21_b33_b42_b51,b11_b22,w=0.0030833240895>']
  42,ChiouYoungs2008: ['<86,b11_b21_b33_b42_b51,b12_b21,w=0.0030833240895>', '<87,b11_b21_b33_b42_b51,b12_b22,w=0.0030833240895>']
  43,Campbell2003: ['<85,b11_b21_b33_b42_b51,b11_b22,w=0.0030833240895>', '<87,b11_b21_b33_b42_b51,b12_b22,w=0.0030833240895>']
  43,ToroEtAl2002: ['<84,b11_b21_b33_b42_b51,b11_b21,w=0.0030833240895>', '<86,b11_b21_b33_b42_b51,b12_b21,w=0.0030833240895>']
  44,BooreAtkinson2008: ['<88,b11_b21_b33_b42_b52,b11_b21,w=0.0030833240895>', '<89,b11_b21_b33_b42_b52,b11_b22,w=0.0030833240895>']
  44,ChiouYoungs2008: ['<90,b11_b21_b33_b42_b52,b12_b21,w=0.0030833240895>', '<91,b11_b21_b33_b42_b52,b12_b22,w=0.0030833240895>']
  45,Campbell2003: ['<89,b11_b21_b33_b42_b52,b11_b22,w=0.0030833240895>', '<91,b11_b21_b33_b42_b52,b12_b22,w=0.0030833240895>']
  45,ToroEtAl2002: ['<88,b11_b21_b33_b42_b52,b11_b21,w=0.0030833240895>', '<90,b11_b21_b33_b42_b52,b12_b21,w=0.0030833240895>']
  46,BooreAtkinson2008: ['<92,b11_b21_b33_b42_b53,b11_b21,w=0.003092583321>', '<93,b11_b21_b33_b42_b53,b11_b22,w=0.003092583321>']
  46,ChiouYoungs2008: ['<94,b11_b21_b33_b42_b53,b12_b21,w=0.003092583321>', '<95,b11_b21_b33_b42_b53,b12_b22,w=0.003092583321>']
  47,Campbell2003: ['<93,b11_b21_b33_b42_b53,b11_b22,w=0.003092583321>', '<95,b11_b21_b33_b42_b53,b12_b22,w=0.003092583321>']
  47,ToroEtAl2002: ['<92,b11_b21_b33_b42_b53,b11_b21,w=0.003092583321>', '<94,b11_b21_b33_b42_b53,b12_b21,w=0.003092583321>']
  48,BooreAtkinson2008: ['<96,b11_b21_b33_b43_b51,b11_b21,w=0.003092583321>', '<97,b11_b21_b33_b43_b51,b11_b22,w=0.003092583321>']
  48,ChiouYoungs2008: ['<98,b11_b21_b33_b43_b51,b12_b21,w=0.003092583321>', '<99,b11_b21_b33_b43_b51,b12_b22,w=0.003092583321>']
  49,Campbell2003: ['<97,b11_b21_b33_b43_b51,b11_b22,w=0.003092583321>', '<99,b11_b21_b33_b43_b51,b12_b22,w=0.003092583321>']
  49,ToroEtAl2002: ['<96,b11_b21_b33_b43_b51,b11_b21,w=0.003092583321>', '<98,b11_b21_b33_b43_b51,b12_b21,w=0.003092583321>']
  50,BooreAtkinson2008: ['<100,b11_b21_b33_b43_b52,b11_b21,w=0.003092583321>', '<101,b11_b21_b33_b43_b52,b11_b22,w=0.003092583321>']
  50,ChiouYoungs2008: ['<102,b11_b21_b33_b43_b52,b12_b21,w=0.003092583321>', '<103,b11_b21_b33_b43_b52,b12_b22,w=0.003092583321>']
  51,Campbell2003: ['<101,b11_b21_b33_b43_b52,b11_b22,w=0.003092583321>', '<103,b11_b21_b33_b43_b52,b12_b22,w=0.003092583321>']
  51,ToroEtAl2002: ['<100,b11_b21_b33_b43_b52,b11_b21,w=0.003092583321>', '<102,b11_b21_b33_b43_b52,b12_b21,w=0.003092583321>']
  52,BooreAtkinson2008: ['<104,b11_b21_b33_b43_b53,b11_b21,w=0.003101870358>', '<105,b11_b21_b33_b43_b53,b11_b22,w=0.003101870358>']
  52,ChiouYoungs2008: ['<106,b11_b21_b33_b43_b53,b12_b21,w=0.003101870358>', '<107,b11_b21_b33_b43_b53,b12_b22,w=0.003101870358>']
  53,Campbell2003: ['<105,b11_b21_b33_b43_b53,b11_b22,w=0.003101870358>', '<107,b11_b21_b33_b43_b53,b12_b22,w=0.003101870358>']
  53,ToroEtAl2002: ['<104,b11_b21_b33_b43_b53,b11_b21,w=0.003101870358>', '<106,b11_b21_b33_b43_b53,b12_b21,w=0.003101870358>']
  54,BooreAtkinson2008: ['<108,b11_b22_b31_b41_b51,b11_b21,w=0.00307409258025>', '<109,b11_b22_b31_b41_b51,b11_b22,w=0.00307409258025>']
  54,ChiouYoungs2008: ['<110,b11_b22_b31_b41_b51,b12_b21,w=0.00307409258025>', '<111,b11_b22_b31_b41_b51,b12_b22,w=0.00307409258025>']
  55,Campbell2003: ['<109,b11_b22_b31_b41_b51,b11_b22,w=0.00307409258025>', '<111,b11_b22_b31_b41_b51,b12_b22,w=0.00307409258025>']
  55,ToroEtAl2002: ['<108,b11_b22_b31_b41_b51,b11_b21,w=0.00307409258025>', '<110,b11_b22_b31_b41_b51,b12_b21,w=0.00307409258025>']
  56,BooreAtkinson2008: ['<112,b11_b22_b31_b41_b52,b11_b21,w=0.00307409258025>', '<113,b11_b22_b31_b41_b52,b11_b22,w=0.00307409258025>']
  56,ChiouYoungs2008: ['<114,b11_b22_b31_b41_b52,b12_b21,w=0.00307409258025>', '<115,b11_b22_b31_b41_b52,b12_b22,w=0.00307409258025>']
  57,Campbell2003: ['<113,b11_b22_b31_b41_b52,b11_b22,w=0.00307409258025>', '<115,b11_b22_b31_b41_b52,b12_b22,w=0.00307409258025>']
  57,ToroEtAl2002: ['<112,b11_b22_b31_b41_b52,b11_b21,w=0.00307409258025>', '<114,b11_b22_b31_b41_b52,b12_b21,w=0.00307409258025>']
  58,BooreAtkinson2008: ['<116,b11_b22_b31_b41_b53,b11_b21,w=0.0030833240895>', '<117,b11_b22_b31_b41_b53,b11_b22,w=0.0030833240895>']
  58,ChiouYoungs2008: ['<118,b11_b22_b31_b41_b53,b12_b21,w=0.0030833240895>', '<119,b11_b22_b31_b41_b53,b12_b22,w=0.0030833240895>']
  59,Campbell2003: ['<117,b11_b22_b31_b41_b53,b11_b22,w=0.0030833240895>', '<119,b11_b22_b31_b41_b53,b12_b22,w=0.0030833240895>']
  59,ToroEtAl2002: ['<116,b11_b22_b31_b41_b53,b11_b21,w=0.0030833240895>', '<118,b11_b22_b31_b41_b53,b12_b21,w=0.0030833240895>']
  60,BooreAtkinson2008: ['<120,b11_b22_b31_b42_b51,b11_b21,w=0.00307409258025>', '<121,b11_b22_b31_b42_b51,b11_b22,w=0.00307409258025>']
  60,ChiouYoungs2008: ['<122,b11_b22_b31_b42_b51,b12_b21,w=0.00307409258025>', '<123,b11_b22_b31_b42_b51,b12_b22,w=0.00307409258025>']
  61,Campbell2003: ['<121,b11_b22_b31_b42_b51,b11_b22,w=0.00307409258025>', '<123,b11_b22_b31_b42_b51,b12_b22,w=0.00307409258025>']
  61,ToroEtAl2002: ['<120,b11_b22_b31_b42_b51,b11_b21,w=0.00307409258025>', '<122,b11_b22_b31_b42_b51,b12_b21,w=0.00307409258025>']
  62,BooreAtkinson2008: ['<124,b11_b22_b31_b42_b52,b11_b21,w=0.00307409258025>', '<125,b11_b22_b31_b42_b52,b11_b22,w=0.00307409258025>']
  62,ChiouYoungs2008: ['<126,b11_b22_b31_b42_b52,b12_b21,w=0.00307409258025>', '<127,b11_b22_b31_b42_b52,b12_b22,w=0.00307409258025>']
  63,Campbell2003: ['<125,b11_b22_b31_b42_b52,b11_b22,w=0.00307409258025>', '<127,b11_b22_b31_b42_b52,b12_b22,w=0.00307409258025>']
  63,ToroEtAl2002: ['<124,b11_b22_b31_b42_b52,b11_b21,w=0.00307409258025>', '<126,b11_b22_b31_b42_b52,b12_b21,w=0.00307409258025>']
  64,BooreAtkinson2008: ['<128,b11_b22_b31_b42_b53,b11_b21,w=0.0030833240895>', '<129,b11_b22_b31_b42_b53,b11_b22,w=0.0030833240895>']
  64,ChiouYoungs2008: ['<130,b11_b22_b31_b42_b53,b12_b21,w=0.0030833240895>', '<131,b11_b22_b31_b42_b53,b12_b22,w=0.0030833240895>']
  65,Campbell2003: ['<129,b11_b22_b31_b42_b53,b11_b22,w=0.0030833240895>', '<131,b11_b22_b31_b42_b53,b12_b22,w=0.0030833240895>']
  65,ToroEtAl2002: ['<128,b11_b22_b31_b42_b53,b11_b21,w=0.0030833240895>', '<130,b11_b22_b31_b42_b53,b12_b21,w=0.0030833240895>']
  66,BooreAtkinson2008: ['<132,b11_b22_b31_b43_b51,b11_b21,w=0.0030833240895>', '<133,b11_b22_b31_b43_b51,b11_b22,w=0.0030833240895>']
  66,ChiouYoungs2008: ['<134,b11_b22_b31_b43_b51,b12_b21,w=0.0030833240895>', '<135,b11_b22_b31_b43_b51,b12_b22,w=0.0030833240895>']
  67,Campbell2003: ['<133,b11_b22_b31_b43_b51,b11_b22,w=0.0030833240895>', '<135,b11_b22_b31_b43_b51,b12_b22,w=0.0030833240895>']
  67,ToroEtAl2002: ['<132,b11_b22_b31_b43_b51,b11_b21,w=0.0030833240895>', '<134,b11_b22_b31_b43_b51,b12_b21,w=0.0030833240895>']
  68,BooreAtkinson2008: ['<136,b11_b22_b31_b43_b52,b11_b21,w=0.0030833240895>', '<137,b11_b22_b31_b43_b52,b11_b22,w=0.0030833240895>']
  68,ChiouYoungs2008: ['<138,b11_b22_b31_b43_b52,b12_b21,w=0.0030833240895>', '<139,b11_b22_b31_b43_b52,b12_b22,w=0.0030833240895>']
  69,Campbell2003: ['<137,b11_b22_b31_b43_b52,b11_b22,w=0.0030833240895>', '<139,b11_b22_b31_b43_b52,b12_b22,w=0.0030833240895>']
  69,ToroEtAl2002: ['<136,b11_b22_b31_b43_b52,b11_b21,w=0.0030833240895>', '<138,b11_b22_b31_b43_b52,b12_b21,w=0.0030833240895>']
  70,BooreAtkinson2008: ['<140,b11_b22_b31_b43_b53,b11_b21,w=0.003092583321>', '<141,b11_b22_b31_b43_b53,b11_b22,w=0.003092583321>']
  70,ChiouYoungs2008: ['<142,b11_b22_b31_b43_b53,b12_b21,w=0.003092583321>', '<143,b11_b22_b31_b43_b53,b12_b22,w=0.003092583321>']
  71,Campbell2003: ['<141,b11_b22_b31_b43_b53,b11_b22,w=0.003092583321>', '<143,b11_b22_b31_b43_b53,b12_b22,w=0.003092583321>']
  71,ToroEtAl2002: ['<140,b11_b22_b31_b43_b53,b11_b21,w=0.003092583321>', '<142,b11_b22_b31_b43_b53,b12_b21,w=0.003092583321>']
  72,BooreAtkinson2008: ['<144,b11_b22_b32_b41_b51,b11_b21,w=0.00307409258025>', '<145,b11_b22_b32_b41_b51,b11_b22,w=0.00307409258025>']
  72,ChiouYoungs2008: ['<146,b11_b22_b32_b41_b51,b12_b21,w=0.00307409258025>', '<147,b11_b22_b32_b41_b51,b12_b22,w=0.00307409258025>']
  73,Campbell2003: ['<145,b11_b22_b32_b41_b51,b11_b22,w=0.00307409258025>', '<147,b11_b22_b32_b41_b51,b12_b22,w=0.00307409258025>']
  73,ToroEtAl2002: ['<144,b11_b22_b32_b41_b51,b11_b21,w=0.00307409258025>', '<146,b11_b22_b32_b41_b51,b12_b21,w=0.00307409258025>']
  74,BooreAtkinson2008: ['<148,b11_b22_b32_b41_b52,b11_b21,w=0.00307409258025>', '<149,b11_b22_b32_b41_b52,b11_b22,w=0.00307409258025>']
  74,ChiouYoungs2008: ['<150,b11_b22_b32_b41_b52,b12_b21,w=0.00307409258025>', '<151,b11_b22_b32_b41_b52,b12_b22,w=0.00307409258025>']
  75,Campbell2003: ['<149,b11_b22_b32_b41_b52,b11_b22,w=0.00307409258025>', '<151,b11_b22_b32_b41_b52,b12_b22,w=0.00307409258025>']
  75,ToroEtAl2002: ['<148,b11_b22_b32_b41_b52,b11_b21,w=0.00307409258025>', '<150,b11_b22_b32_b41_b52,b12_b21,w=0.00307409258025>']
  76,BooreAtkinson2008: ['<152,b11_b22_b32_b41_b53,b11_b21,w=0.0030833240895>', '<153,b11_b22_b32_b41_b53,b11_b22,w=0.0030833240895>']
  76,ChiouYoungs2008: ['<154,b11_b22_b32_b41_b53,b12_b21,w=0.0030833240895>', '<155,b11_b22_b32_b41_b53,b12_b22,w=0.0030833240895>']
  77,Campbell2003: ['<153,b11_b22_b32_b41_b53,b11_b22,w=0.0030833240895>', '<155,b11_b22_b32_b41_b53,b12_b22,w=0.0030833240895>']
  77,ToroEtAl2002: ['<152,b11_b22_b32_b41_b53,b11_b21,w=0.0030833240895>', '<154,b11_b22_b32_b41_b53,b12_b21,w=0.0030833240895>']
  78,BooreAtkinson2008: ['<156,b11_b22_b32_b42_b51,b11_b21,w=0.00307409258025>', '<157,b11_b22_b32_b42_b51,b11_b22,w=0.00307409258025>']
  78,ChiouYoungs2008: ['<158,b11_b22_b32_b42_b51,b12_b21,w=0.00307409258025>', '<159,b11_b22_b32_b42_b51,b12_b22,w=0.00307409258025>']
  79,Campbell2003: ['<157,b11_b22_b32_b42_b51,b11_b22,w=0.00307409258025>', '<159,b11_b22_b32_b42_b51,b12_b22,w=0.00307409258025>']
  79,ToroEtAl2002: ['<156,b11_b22_b32_b42_b51,b11_b21,w=0.00307409258025>', '<158,b11_b22_b32_b42_b51,b12_b21,w=0.00307409258025>']
  80,BooreAtkinson2008: ['<160,b11_b22_b32_b42_b52,b11_b21,w=0.00307409258025>', '<161,b11_b22_b32_b42_b52,b11_b22,w=0.00307409258025>']
  80,ChiouYoungs2008: ['<162,b11_b22_b32_b42_b52,b12_b21,w=0.00307409258025>', '<163,b11_b22_b32_b42_b52,b12_b22,w=0.00307409258025>']
  81,Campbell2003: ['<161,b11_b22_b32_b42_b52,b11_b22,w=0.00307409258025>', '<163,b11_b22_b32_b42_b52,b12_b22,w=0.00307409258025>']
  81,ToroEtAl2002: ['<160,b11_b22_b32_b42_b52,b11_b21,w=0.00307409258025>', '<162,b11_b22_b32_b42_b52,b12_b21,w=0.00307409258025>']
  82,BooreAtkinson2008: ['<164,b11_b22_b32_b42_b53,b11_b21,w=0.0030833240895>', '<165,b11_b22_b32_b42_b53,b11_b22,w=0.0030833240895>']
  82,ChiouYoungs2008: ['<166,b11_b22_b32_b42_b53,b12_b21,w=0.0030833240895>', '<167,b11_b22_b32_b42_b53,b12_b22,w=0.0030833240895>']
  83,Campbell2003: ['<165,b11_b22_b32_b42_b53,b11_b22,w=0.0030833240895>', '<167,b11_b22_b32_b42_b53,b12_b22,w=0.0030833240895>']
  83,ToroEtAl2002: ['<164,b11_b22_b32_b42_b53,b11_b21,w=0.0030833240895>', '<166,b11_b22_b32_b42_b53,b12_b21,w=0.0030833240895>']
  84,BooreAtkinson2008: ['<168,b11_b22_b32_b43_b51,b11_b21,w=0.0030833240895>', '<169,b11_b22_b32_b43_b51,b11_b22,w=0.0030833240895>']
  84,ChiouYoungs2008: ['<170,b11_b22_b32_b43_b51,b12_b21,w=0.0030833240895>', '<171,b11_b22_b32_b43_b51,b12_b22,w=0.0030833240895>']
  85,Campbell2003: ['<169,b11_b22_b32_b43_b51,b11_b22,w=0.0030833240895>', '<171,b11_b22_b32_b43_b51,b12_b22,w=0.0030833240895>']
  85,ToroEtAl2002: ['<168,b11_b22_b32_b43_b51,b11_b21,w=0.0030833240895>', '<170,b11_b22_b32_b43_b51,b12_b21,w=0.0030833240895>']
  86,BooreAtkinson2008: ['<172,b11_b22_b32_b43_b52,b11_b21,w=0.0030833240895>', '<173,b11_b22_b32_b43_b52,b11_b22,w=0.0030833240895>']
  86,ChiouYoungs2008: ['<174,b11_b22_b32_b43_b52,b12_b21,w=0.0030833240895>', '<175,b11_b22_b32_b43_b52,b12_b22,w=0.0030833240895>']
  87,Campbell2003: ['<173,b11_b22_b32_b43_b52,b11_b22,w=0.0030833240895>', '<175,b11_b22_b32_b43_b52,b12_b22,w=0.0030833240895>']
  87,ToroEtAl2002: ['<172,b11_b22_b32_b43_b52,b11_b21,w=0.0030833240895>', '<174,b11_b22_b32_b43_b52,b12_b21,w=0.0030833240895>']
  88,BooreAtkinson2008: ['<176,b11_b22_b32_b43_b53,b11_b21,w=0.003092583321>', '<177,b11_b22_b32_b43_b53,b11_b22,w=0.003092583321>']
  88,ChiouYoungs2008: ['<178,b11_b22_b32_b43_b53,b12_b21,w=0.003092583321>', '<179,b11_b22_b32_b43_b53,b12_b22,w=0.003092583321>']
  89,Campbell2003: ['<177,b11_b22_b32_b43_b53,b11_b22,w=0.003092583321>', '<179,b11_b22_b32_b43_b53,b12_b22,w=0.003092583321>']
  89,ToroEtAl2002: ['<176,b11_b22_b32_b43_b53,b11_b21,w=0.003092583321>', '<178,b11_b22_b32_b43_b53,b12_b21,w=0.003092583321>']
  90,BooreAtkinson2008: ['<180,b11_b22_b33_b41_b51,b11_b21,w=0.0030833240895>', '<181,b11_b22_b33_b41_b51,b11_b22,w=0.0030833240895>']
  90,ChiouYoungs2008: ['<182,b11_b22_b33_b41_b51,b12_b21,w=0.0030833240895>', '<183,b11_b22_b33_b41_b51,b12_b22,w=0.0030833240895>']
  91,Campbell2003: ['<181,b11_b22_b33_b41_b51,b11_b22,w=0.0030833240895>', '<183,b11_b22_b33_b41_b51,b12_b22,w=0.0030833240895>']
  91,ToroEtAl2002: ['<180,b11_b22_b33_b41_b51,b11_b21,w=0.0030833240895>', '<182,b11_b22_b33_b41_b51,b12_b21,w=0.0030833240895>']
  92,BooreAtkinson2008: ['<184,b11_b22_b33_b41_b52,b11_b21,w=0.0030833240895>', '<185,b11_b22_b33_b41_b52,b11_b22,w=0.0030833240895>']
  92,ChiouYoungs2008: ['<186,b11_b22_b33_b41_b52,b12_b21,w=0.0030833240895>', '<187,b11_b22_b33_b41_b52,b12_b22,w=0.0030833240895>']
  93,Campbell2003: ['<185,b11_b22_b33_b41_b52,b11_b22,w=0.0030833240895>', '<187,b11_b22_b33_b41_b52,b12_b22,w=0.0030833240895>']
  93,ToroEtAl2002: ['<184,b11_b22_b33_b41_b52,b11_b21,w=0.0030833240895>', '<186,b11_b22_b33_b41_b52,b12_b21,w=0.0030833240895>']
  94,BooreAtkinson2008: ['<188,b11_b22_b33_b41_b53,b11_b21,w=0.003092583321>', '<189,b11_b22_b33_b41_b53,b11_b22,w=0.003092583321>']
  94,ChiouYoungs2008: ['<190,b11_b22_b33_b41_b53,b12_b21,w=0.003092583321>', '<191,b11_b22_b33_b41_b53,b12_b22,w=0.003092583321>']
  95,Campbell2003: ['<189,b11_b22_b33_b41_b53,b11_b22,w=0.003092583321>', '<191,b11_b22_b33_b41_b53,b12_b22,w=0.003092583321>']
  95,ToroEtAl2002: ['<188,b11_b22_b33_b41_b53,b11_b21,w=0.003092583321>', '<190,b11_b22_b33_b41_b53,b12_b21,w=0.003092583321>']
  96,BooreAtkinson2008: ['<192,b11_b22_b33_b42_b51,b11_b21,w=0.0030833240895>', '<193,b11_b22_b33_b42_b51,b11_b22,w=0.0030833240895>']
  96,ChiouYoungs2008: ['<194,b11_b22_b33_b42_b51,b12_b21,w=0.0030833240895>', '<195,b11_b22_b33_b42_b51,b12_b22,w=0.0030833240895>']
  97,Campbell2003: ['<193,b11_b22_b33_b42_b51,b11_b22,w=0.0030833240895>', '<195,b11_b22_b33_b42_b51,b12_b22,w=0.0030833240895>']
  97,ToroEtAl2002: ['<192,b11_b22_b33_b42_b51,b11_b21,w=0.0030833240895>', '<194,b11_b22_b33_b42_b51,b12_b21,w=0.0030833240895>']
  98,BooreAtkinson2008: ['<196,b11_b22_b33_b42_b52,b11_b21,w=0.0030833240895>', '<197,b11_b22_b33_b42_b52,b11_b22,w=0.0030833240895>']
  98,ChiouYoungs2008: ['<198,b11_b22_b33_b42_b52,b12_b21,w=0.0030833240895>', '<199,b11_b22_b33_b42_b52,b12_b22,w=0.0030833240895>']
  99,Campbell2003: ['<197,b11_b22_b33_b42_b52,b11_b22,w=0.0030833240895>', '<199,b11_b22_b33_b42_b52,b12_b22,w=0.0030833240895>']
  99,ToroEtAl2002: ['<196,b11_b22_b33_b42_b52,b11_b21,w=0.0030833240895>', '<198,b11_b22_b33_b42_b52,b12_b21,w=0.0030833240895>']
  100,BooreAtkinson2008: ['<200,b11_b22_b33_b42_b53,b11_b21,w=0.003092583321>', '<201,b11_b22_b33_b42_b53,b11_b22,w=0.003092583321>']
  100,ChiouYoungs2008: ['<202,b11_b22_b33_b42_b53,b12_b21,w=0.003092583321>', '<203,b11_b22_b33_b42_b53,b12_b22,w=0.003092583321>']
  101,Campbell2003: ['<201,b11_b22_b33_b42_b53,b11_b22,w=0.003092583321>', '<203,b11_b22_b33_b42_b53,b12_b22,w=0.003092583321>']
  101,ToroEtAl2002: ['<200,b11_b22_b33_b42_b53,b11_b21,w=0.003092583321>', '<202,b11_b22_b33_b42_b53,b12_b21,w=0.003092583321>']
  102,BooreAtkinson2008: ['<204,b11_b22_b33_b43_b51,b11_b21,w=0.003092583321>', '<205,b11_b22_b33_b43_b51,b11_b22,w=0.003092583321>']
  102,ChiouYoungs2008: ['<206,b11_b22_b33_b43_b51,b12_b21,w=0.003092583321>', '<207,b11_b22_b33_b43_b51,b12_b22,w=0.003092583321>']
  103,Campbell2003: ['<205,b11_b22_b33_b43_b51,b11_b22,w=0.003092583321>', '<207,b11_b22_b33_b43_b51,b12_b22,w=0.003092583321>']
  103,ToroEtAl2002: ['<204,b11_b22_b33_b43_b51,b11_b21,w=0.003092583321>', '<206,b11_b22_b33_b43_b51,b12_b21,w=0.003092583321>']
  104,BooreAtkinson2008: ['<208,b11_b22_b33_b43_b52,b11_b21,w=0.003092583321>', '<209,b11_b22_b33_b43_b52,b11_b22,w=0.003092583321>']
  104,ChiouYoungs2008: ['<210,b11_b22_b33_b43_b52,b12_b21,w=0.003092583321>', '<211,b11_b22_b33_b43_b52,b12_b22,w=0.003092583321>']
  105,Campbell2003: ['<209,b11_b22_b33_b43_b52,b11_b22,w=0.003092583321>', '<211,b11_b22_b33_b43_b52,b12_b22,w=0.003092583321>']
  105,ToroEtAl2002: ['<208,b11_b22_b33_b43_b52,b11_b21,w=0.003092583321>', '<210,b11_b22_b33_b43_b52,b12_b21,w=0.003092583321>']
  106,BooreAtkinson2008: ['<212,b11_b22_b33_b43_b53,b11_b21,w=0.003101870358>', '<213,b11_b22_b33_b43_b53,b11_b22,w=0.003101870358>']
  106,ChiouYoungs2008: ['<214,b11_b22_b33_b43_b53,b12_b21,w=0.003101870358>', '<215,b11_b22_b33_b43_b53,b12_b22,w=0.003101870358>']
  107,Campbell2003: ['<213,b11_b22_b33_b43_b53,b11_b22,w=0.003101870358>', '<215,b11_b22_b33_b43_b53,b12_b22,w=0.003101870358>']
  107,ToroEtAl2002: ['<212,b11_b22_b33_b43_b53,b11_b21,w=0.003101870358>', '<214,b11_b22_b33_b43_b53,b12_b21,w=0.003101870358>']
  108,BooreAtkinson2008: ['<216,b11_b23_b31_b41_b51,b11_b21,w=0.0030833240895>', '<217,b11_b23_b31_b41_b51,b11_b22,w=0.0030833240895>']
  108,ChiouYoungs2008: ['<218,b11_b23_b31_b41_b51,b12_b21,w=0.0030833240895>', '<219,b11_b23_b31_b41_b51,b12_b22,w=0.0030833240895>']
  109,Campbell2003: ['<217,b11_b23_b31_b41_b51,b11_b22,w=0.0030833240895>', '<219,b11_b23_b31_b41_b51,b12_b22,w=0.0030833240895>']
  109,ToroEtAl2002: ['<216,b11_b23_b31_b41_b51,b11_b21,w=0.0030833240895>', '<218,b11_b23_b31_b41_b51,b12_b21,w=0.0030833240895>']
  110,BooreAtkinson2008: ['<220,b11_b23_b31_b41_b52,b11_b21,w=0.0030833240895>', '<221,b11_b23_b31_b41_b52,b11_b22,w=0.0030833240895>']
  110,ChiouYoungs2008: ['<222,b11_b23_b31_b41_b52,b12_b21,w=0.0030833240895>', '<223,b11_b23_b31_b41_b52,b12_b22,w=0.0030833240895>']
  111,Campbell2003: ['<221,b11_b23_b31_b41_b52,b11_b22,w=0.0030833240895>', '<223,b11_b23_b31_b41_b52,b12_b22,w=0.0030833240895>']
  111,ToroEtAl2002: ['<220,b11_b23_b31_b41_b52,b11_b21,w=0.0030833240895>', '<222,b11_b23_b31_b41_b52,b12_b21,w=0.0030833240895>']
  112,BooreAtkinson2008: ['<224,b11_b23_b31_b41_b53,b11_b21,w=0.003092583321>', '<225,b11_b23_b31_b41_b53,b11_b22,w=0.003092583321>']
  112,ChiouYoungs2008: ['<226,b11_b23_b31_b41_b53,b12_b21,w=0.003092583321>', '<227,b11_b23_b31_b41_b53,b12_b22,w=0.003092583321>']
  113,Campbell2003: ['<225,b11_b23_b31_b41_b53,b11_b22,w=0.003092583321>', '<227,b11_b23_b31_b41_b53,b12_b22,w=0.003092583321>']
  113,ToroEtAl2002: ['<224,b11_b23_b31_b41_b53,b11_b21,w=0.003092583321>', '<226,b11_b23_b31_b41_b53,b12_b21,w=0.003092583321>']
  114,BooreAtkinson2008: ['<228,b11_b23_b31_b42_b51,b11_b21,w=0.0030833240895>', '<229,b11_b23_b31_b42_b51,b11_b22,w=0.0030833240895>']
  114,ChiouYoungs2008: ['<230,b11_b23_b31_b42_b51,b12_b21,w=0.0030833240895>', '<231,b11_b23_b31_b42_b51,b12_b22,w=0.0030833240895>']
  115,Campbell2003: ['<229,b11_b23_b31_b42_b51,b11_b22,w=0.0030833240895>', '<231,b11_b23_b31_b42_b51,b12_b22,w=0.0030833240895>']
  115,ToroEtAl2002: ['<228,b11_b23_b31_b42_b51,b11_b21,w=0.0030833240895>', '<230,b11_b23_b31_b42_b51,b12_b21,w=0.0030833240895>']
  116,BooreAtkinson2008: ['<232,b11_b23_b31_b42_b52,b11_b21,w=0.0030833240895>', '<233,b11_b23_b31_b42_b52,b11_b22,w=0.0030833240895>']
  116,ChiouYoungs2008: ['<234,b11_b23_b31_b42_b52,b12_b21,w=0.0030833240895>', '<235,b11_b23_b31_b42_b52,b12_b22,w=0.0030833240895>']
  117,Campbell2003: ['<233,b11_b23_b31_b42_b52,b11_b22,w=0.0030833240895>', '<235,b11_b23_b31_b42_b52,b12_b22,w=0.0030833240895>']
  117,ToroEtAl2002: ['<232,b11_b23_b31_b42_b52,b11_b21,w=0.0030833240895>', '<234,b11_b23_b31_b42_b52,b12_b21,w=0.0030833240895>']
  118,BooreAtkinson2008: ['<236,b11_b23_b31_b42_b53,b11_b21,w=0.003092583321>', '<237,b11_b23_b31_b42_b53,b11_b22,w=0.003092583321>']
  118,ChiouYoungs2008: ['<238,b11_b23_b31_b42_b53,b12_b21,w=0.003092583321>', '<239,b11_b23_b31_b42_b53,b12_b22,w=0.003092583321>']
  119,Campbell2003: ['<237,b11_b23_b31_b42_b53,b11_b22,w=0.003092583321>', '<239,b11_b23_b31_b42_b53,b12_b22,w=0.003092583321>']
  119,ToroEtAl2002: ['<236,b11_b23_b31_b42_b53,b11_b21,w=0.003092583321>', '<238,b11_b23_b31_b42_b53,b12_b21,w=0.003092583321>']
  120,BooreAtkinson2008: ['<240,b11_b23_b31_b43_b51,b11_b21,w=0.003092583321>', '<241,b11_b23_b31_b43_b51,b11_b22,w=0.003092583321>']
  120,ChiouYoungs2008: ['<242,b11_b23_b31_b43_b51,b12_b21,w=0.003092583321>', '<243,b11_b23_b31_b43_b51,b12_b22,w=0.003092583321>']
  121,Campbell2003: ['<241,b11_b23_b31_b43_b51,b11_b22,w=0.003092583321>', '<243,b11_b23_b31_b43_b51,b12_b22,w=0.003092583321>']
  121,ToroEtAl2002: ['<240,b11_b23_b31_b43_b51,b11_b21,w=0.003092583321>', '<242,b11_b23_b31_b43_b51,b12_b21,w=0.003092583321>']
  122,BooreAtkinson2008: ['<244,b11_b23_b31_b43_b52,b11_b21,w=0.003092583321>', '<245,b11_b23_b31_b43_b52,b11_b22,w=0.003092583321>']
  122,ChiouYoungs2008: ['<246,b11_b23_b31_b43_b52,b12_b21,w=0.003092583321>', '<247,b11_b23_b31_b43_b52,b12_b22,w=0.003092583321>']
  123,Campbell2003: ['<245,b11_b23_b31_b43_b52,b11_b22,w=0.003092583321>', '<247,b11_b23_b31_b43_b52,b12_b22,w=0.003092583321>']
  123,ToroEtAl2002: ['<244,b11_b23_b31_b43_b52,b11_b21,w=0.003092583321>', '<246,b11_b23_b31_b43_b52,b12_b21,w=0.003092583321>']
  124,BooreAtkinson2008: ['<248,b11_b23_b31_b43_b53,b11_b21,w=0.003101870358>', '<249,b11_b23_b31_b43_b53,b11_b22,w=0.003101870358>']
  124,ChiouYoungs2008: ['<250,b11_b23_b31_b43_b53,b12_b21,w=0.003101870358>', '<251,b11_b23_b31_b43_b53,b12_b22,w=0.003101870358>']
  125,Campbell2003: ['<249,b11_b23_b31_b43_b53,b11_b22,w=0.003101870358>', '<251,b11_b23_b31_b43_b53,b12_b22,w=0.003101870358>']
  125,ToroEtAl2002: ['<248,b11_b23_b31_b43_b53,b11_b21,w=0.003101870358>', '<250,b11_b23_b31_b43_b53,b12_b21,w=0.003101870358>']
  126,BooreAtkinson2008: ['<252,b11_b23_b32_b41_b51,b11_b21,w=0.0030833240895>', '<253,b11_b23_b32_b41_b51,b11_b22,w=0.0030833240895>']
  126,ChiouYoungs2008: ['<254,b11_b23_b32_b41_b51,b12_b21,w=0.0030833240895>', '<255,b11_b23_b32_b41_b51,b12_b22,w=0.0030833240895>']
  127,Campbell2003: ['<253,b11_b23_b32_b41_b51,b11_b22,w=0.0030833240895>', '<255,b11_b23_b32_b41_b51,b12_b22,w=0.0030833240895>']
  127,ToroEtAl2002: ['<252,b11_b23_b32_b41_b51,b11_b21,w=0.0030833240895>', '<254,b11_b23_b32_b41_b51,b12_b21,w=0.0030833240895>']
  128,BooreAtkinson2008: ['<256,b11_b23_b32_b41_b52,b11_b21,w=0.0030833240895>', '<257,b11_b23_b32_b41_b52,b11_b22,w=0.0030833240895>']
  128,ChiouYoungs2008: ['<258,b11_b23_b32_b41_b52,b12_b21,w=0.0030833240895>', '<259,b11_b23_b32_b41_b52,b12_b22,w=0.0030833240895>']
  129,Campbell2003: ['<257,b11_b23_b32_b41_b52,b11_b22,w=0.0030833240895>', '<259,b11_b23_b32_b41_b52,b12_b22,w=0.0030833240895>']
  129,ToroEtAl2002: ['<256,b11_b23_b32_b41_b52,b11_b21,w=0.0030833240895>', '<258,b11_b23_b32_b41_b52,b12_b21,w=0.0030833240895>']
  130,BooreAtkinson2008: ['<260,b11_b23_b32_b41_b53,b11_b21,w=0.003092583321>', '<261,b11_b23_b32_b41_b53,b11_b22,w=0.003092583321>']
  130,ChiouYoungs2008: ['<262,b11_b23_b32_b41_b53,b12_b21,w=0.003092583321>', '<263,b11_b23_b32_b41_b53,b12_b22,w=0.003092583321>']
  131,Campbell2003: ['<261,b11_b23_b32_b41_b53,b11_b22,w=0.003092583321>', '<263,b11_b23_b32_b41_b53,b12_b22,w=0.003092583321>']
  131,ToroEtAl2002: ['<260,b11_b23_b32_b41_b53,b11_b21,w=0.003092583321>', '<262,b11_b23_b32_b41_b53,b12_b21,w=0.003092583321>']
  132,BooreAtkinson2008: ['<264,b11_b23_b32_b42_b51,b11_b21,w=0.0030833240895>', '<265,b11_b23_b32_b42_b51,b11_b22,w=0.0030833240895>']
  132,ChiouYoungs2008: ['<266,b11_b23_b32_b42_b51,b12_b21,w=0.0030833240895>', '<267,b11_b23_b32_b42_b51,b12_b22,w=0.0030833240895>']
  133,Campbell2003: ['<265,b11_b23_b32_b42_b51,b11_b22,w=0.0030833240895>', '<267,b11_b23_b32_b42_b51,b12_b22,w=0.0030833240895>']
  133,ToroEtAl2002: ['<264,b11_b23_b32_b42_b51,b11_b21,w=0.0030833240895>', '<266,b11_b23_b32_b42_b51,b12_b21,w=0.0030833240895>']
  134,BooreAtkinson2008: ['<268,b11_b23_b32_b42_b52,b11_b21,w=0.0030833240895>', '<269,b11_b23_b32_b42_b52,b11_b22,w=0.0030833240895>']
  134,ChiouYoungs2008: ['<270,b11_b23_b32_b42_b52,b12_b21,w=0.0030833240895>', '<271,b11_b23_b32_b42_b52,b12_b22,w=0.0030833240895>']
  135,Campbell2003: ['<269,b11_b23_b32_b42_b52,b11_b22,w=0.0030833240895>', '<271,b11_b23_b32_b42_b52,b12_b22,w=0.0030833240895>']
  135,ToroEtAl2002: ['<268,b11_b23_b32_b42_b52,b11_b21,w=0.0030833240895>', '<270,b11_b23_b32_b42_b52,b12_b21,w=0.0030833240895>']
  136,BooreAtkinson2008: ['<272,b11_b23_b32_b42_b53,b11_b21,w=0.003092583321>', '<273,b11_b23_b32_b42_b53,b11_b22,w=0.003092583321>']
  136,ChiouYoungs2008: ['<274,b11_b23_b32_b42_b53,b12_b21,w=0.003092583321>', '<275,b11_b23_b32_b42_b53,b12_b22,w=0.003092583321>']
  137,Campbell2003: ['<273,b11_b23_b32_b42_b53,b11_b22,w=0.003092583321>', '<275,b11_b23_b32_b42_b53,b12_b22,w=0.003092583321>']
  137,ToroEtAl2002: ['<272,b11_b23_b32_b42_b53,b11_b21,w=0.003092583321>', '<274,b11_b23_b32_b42_b53,b12_b21,w=0.003092583321>']
  138,BooreAtkinson2008: ['<276,b11_b23_b32_b43_b51,b11_b21,w=0.003092583321>', '<277,b11_b23_b32_b43_b51,b11_b22,w=0.003092583321>']
  138,ChiouYoungs2008: ['<278,b11_b23_b32_b43_b51,b12_b21,w=0.003092583321>', '<279,b11_b23_b32_b43_b51,b12_b22,w=0.003092583321>']
  139,Campbell2003: ['<277,b11_b23_b32_b43_b51,b11_b22,w=0.003092583321>', '<279,b11_b23_b32_b43_b51,b12_b22,w=0.003092583321>']
  139,ToroEtAl2002: ['<276,b11_b23_b32_b43_b51,b11_b21,w=0.003092583321>', '<278,b11_b23_b32_b43_b51,b12_b21,w=0.003092583321>']
  140,BooreAtkinson2008: ['<280,b11_b23_b32_b43_b52,b11_b21,w=0.003092583321>', '<281,b11_b23_b32_b43_b52,b11_b22,w=0.003092583321>']
  140,ChiouYoungs2008: ['<282,b11_b23_b32_b43_b52,b12_b21,w=0.003092583321>', '<283,b11_b23_b32_b43_b52,b12_b22,w=0.003092583321>']
  141,Campbell2003: ['<281,b11_b23_b32_b43_b52,b11_b22,w=0.003092583321>', '<283,b11_b23_b32_b43_b52,b12_b22,w=0.003092583321>']
  141,ToroEtAl2002: ['<280,b11_b23_b32_b43_b52,b11_b21,w=0.003092583321>', '<282,b11_b23_b32_b43_b52,b12_b21,w=0.003092583321>']
  142,BooreAtkinson2008: ['<284,b11_b23_b32_b43_b53,b11_b21,w=0.003101870358>', '<285,b11_b23_b32_b43_b53,b11_b22,w=0.003101870358>']
  142,ChiouYoungs2008: ['<286,b11_b23_b32_b43_b53,b12_b21,w=0.003101870358>', '<287,b11_b23_b32_b43_b53,b12_b22,w=0.003101870358>']
  143,Campbell2003: ['<285,b11_b23_b32_b43_b53,b11_b22,w=0.003101870358>', '<287,b11_b23_b32_b43_b53,b12_b22,w=0.003101870358>']
  143,ToroEtAl2002: ['<284,b11_b23_b32_b43_b53,b11_b21,w=0.003101870358>', '<286,b11_b23_b32_b43_b53,b12_b21,w=0.003101870358>']
  144,BooreAtkinson2008: ['<288,b11_b23_b33_b41_b51,b11_b21,w=0.003092583321>', '<289,b11_b23_b33_b41_b51,b11_b22,w=0.003092583321>']
  144,ChiouYoungs2008: ['<290,b11_b23_b33_b41_b51,b12_b21,w=0.003092583321>', '<291,b11_b23_b33_b41_b51,b12_b22,w=0.003092583321>']
  145,Campbell2003: ['<289,b11_b23_b33_b41_b51,b11_b22,w=0.003092583321>', '<291,b11_b23_b33_b41_b51,b12_b22,w=0.003092583321>']
  145,ToroEtAl2002: ['<288,b11_b23_b33_b41_b51,b11_b21,w=0.003092583321>', '<290,b11_b23_b33_b41_b51,b12_b21,w=0.003092583321>']
  146,BooreAtkinson2008: ['<292,b11_b23_b33_b41_b52,b11_b21,w=0.003092583321>', '<293,b11_b23_b33_b41_b52,b11_b22,w=0.003092583321>']
  146,ChiouYoungs2008: ['<294,b11_b23_b33_b41_b52,b12_b21,w=0.003092583321>', '<295,b11_b23_b33_b41_b52,b12_b22,w=0.003092583321>']
  147,Campbell2003: ['<293,b11_b23_b33_b41_b52,b11_b22,w=0.003092583321>', '<295,b11_b23_b33_b41_b52,b12_b22,w=0.003092583321>']
  147,ToroEtAl2002: ['<292,b11_b23_b33_b41_b52,b11_b21,w=0.003092583321>', '<294,b11_b23_b33_b41_b52,b12_b21,w=0.003092583321>']
  148,BooreAtkinson2008: ['<296,b11_b23_b33_b41_b53,b11_b21,w=0.003101870358>', '<297,b11_b23_b33_b41_b53,b11_b22,w=0.003101870358>']
  148,ChiouYoungs2008: ['<298,b11_b23_b33_b41_b53,b12_b21,w=0.003101870358>', '<299,b11_b23_b33_b41_b53,b12_b22,w=0.003101870358>']
  149,Campbell2003: ['<297,b11_b23_b33_b41_b53,b11_b22,w=0.003101870358>', '<299,b11_b23_b33_b41_b53,b12_b22,w=0.003101870358>']
  149,ToroEtAl2002: ['<296,b11_b23_b33_b41_b53,b11_b21,w=0.003101870358>', '<298,b11_b23_b33_b41_b53,b12_b21,w=0.003101870358>']
  150,BooreAtkinson2008: ['<300,b11_b23_b33_b42_b51,b11_b21,w=0.003092583321>', '<301,b11_b23_b33_b42_b51,b11_b22,w=0.003092583321>']
  150,ChiouYoungs2008: ['<302,b11_b23_b33_b42_b51,b12_b21,w=0.003092583321>', '<303,b11_b23_b33_b42_b51,b12_b22,w=0.003092583321>']
  151,Campbell2003: ['<301,b11_b23_b33_b42_b51,b11_b22,w=0.003092583321>', '<303,b11_b23_b33_b42_b51,b12_b22,w=0.003092583321>']
  151,ToroEtAl2002: ['<300,b11_b23_b33_b42_b51,b11_b21,w=0.003092583321>', '<302,b11_b23_b33_b42_b51,b12_b21,w=0.003092583321>']
  152,BooreAtkinson2008: ['<304,b11_b23_b33_b42_b52,b11_b21,w=0.003092583321>', '<305,b11_b23_b33_b42_b52,b11_b22,w=0.003092583321>']
  152,ChiouYoungs2008: ['<306,b11_b23_b33_b42_b52,b12_b21,w=0.003092583321>', '<307,b11_b23_b33_b42_b52,b12_b22,w=0.003092583321>']
  153,Campbell2003: ['<305,b11_b23_b33_b42_b52,b11_b22,w=0.003092583321>', '<307,b11_b23_b33_b42_b52,b12_b22,w=0.003092583321>']
  153,ToroEtAl2002: ['<304,b11_b23_b33_b42_b52,b11_b21,w=0.003092583321>', '<306,b11_b23_b33_b42_b52,b12_b21,w=0.003092583321>']
  154,BooreAtkinson2008: ['<308,b11_b23_b33_b42_b53,b11_b21,w=0.003101870358>', '<309,b11_b23_b33_b42_b53,b11_b22,w=0.003101870358>']
  154,ChiouYoungs2008: ['<310,b11_b23_b33_b42_b53,b12_b21,w=0.003101870358>', '<311,b11_b23_b33_b42_b53,b12_b22,w=0.003101870358>']
  155,Campbell2003: ['<309,b11_b23_b33_b42_b53,b11_b22,w=0.003101870358>', '<311,b11_b23_b33_b42_b53,b12_b22,w=0.003101870358>']
  155,ToroEtAl2002: ['<308,b11_b23_b33_b42_b53,b11_b21,w=0.003101870358>', '<310,b11_b23_b33_b42_b53,b12_b21,w=0.003101870358>']
  156,BooreAtkinson2008: ['<312,b11_b23_b33_b43_b51,b11_b21,w=0.003101870358>', '<313,b11_b23_b33_b43_b51,b11_b22,w=0.003101870358>']
  156,ChiouYoungs2008: ['<314,b11_b23_b33_b43_b51,b12_b21,w=0.003101870358>', '<315,b11_b23_b33_b43_b51,b12_b22,w=0.003101870358>']
  157,Campbell2003: ['<313,b11_b23_b33_b43_b51,b11_b22,w=0.003101870358>', '<315,b11_b23_b33_b43_b51,b12_b22,w=0.003101870358>']
  157,ToroEtAl2002: ['<312,b11_b23_b33_b43_b51,b11_b21,w=0.003101870358>', '<314,b11_b23_b33_b43_b51,b12_b21,w=0.003101870358>']
  158,BooreAtkinson2008: ['<316,b11_b23_b33_b43_b52,b11_b21,w=0.003101870358>', '<317,b11_b23_b33_b43_b52,b11_b22,w=0.003101870358>']
  158,ChiouYoungs2008: ['<318,b11_b23_b33_b43_b52,b12_b21,w=0.003101870358>', '<319,b11_b23_b33_b43_b52,b12_b22,w=0.003101870358>']
  159,Campbell2003: ['<317,b11_b23_b33_b43_b52,b11_b22,w=0.003101870358>', '<319,b11_b23_b33_b43_b52,b12_b22,w=0.003101870358>']
  159,ToroEtAl2002: ['<316,b11_b23_b33_b43_b52,b11_b21,w=0.003101870358>', '<318,b11_b23_b33_b43_b52,b12_b21,w=0.003101870358>']
  160,BooreAtkinson2008: ['<320,b11_b23_b33_b43_b53,b11_b21,w=0.003111185284>', '<321,b11_b23_b33_b43_b53,b11_b22,w=0.003111185284>']
  160,ChiouYoungs2008: ['<322,b11_b23_b33_b43_b53,b12_b21,w=0.003111185284>', '<323,b11_b23_b33_b43_b53,b12_b22,w=0.003111185284>']
  161,Campbell2003: ['<321,b11_b23_b33_b43_b53,b11_b22,w=0.003111185284>', '<323,b11_b23_b33_b43_b53,b12_b22,w=0.003111185284>']
  161,ToroEtAl2002: ['<320,b11_b23_b33_b43_b53,b11_b21,w=0.003111185284>', '<322,b11_b23_b33_b43_b53,b12_b21,w=0.003111185284>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ======================== =========== ============ ======
source_model     trt_id trt                      num_sources eff_ruptures weight
================ ====== ======================== =========== ============ ======
source_model.xml 0      Active Shallow Crust     1           1,334        1,334 
source_model.xml 1      Stable Continental Crust 1           4,100        102   
source_model.xml 2      Active Shallow Crust     1           1,337        1,337 
source_model.xml 3      Stable Continental Crust 1           4,100        102   
source_model.xml 4      Active Shallow Crust     1           1,339        1,339 
source_model.xml 5      Stable Continental Crust 1           4,100        102   
source_model.xml 6      Active Shallow Crust     1           1,334        1,334 
source_model.xml 7      Stable Continental Crust 1           4,715        117   
source_model.xml 8      Active Shallow Crust     1           1,337        1,337 
source_model.xml 9      Stable Continental Crust 1           4,715        117   
source_model.xml 10     Active Shallow Crust     1           1,339        1,339 
source_model.xml 11     Stable Continental Crust 1           4,715        117   
source_model.xml 12     Active Shallow Crust     1           1,334        1,334 
source_model.xml 13     Stable Continental Crust 1           5,330        133   
source_model.xml 14     Active Shallow Crust     1           1,337        1,337 
source_model.xml 15     Stable Continental Crust 1           5,330        133   
source_model.xml 16     Active Shallow Crust     1           1,339        1,339 
source_model.xml 17     Stable Continental Crust 1           5,330        133   
source_model.xml 18     Active Shallow Crust     1           1,334        1,334 
source_model.xml 19     Stable Continental Crust 1           4,100        102   
source_model.xml 20     Active Shallow Crust     1           1,337        1,337 
source_model.xml 21     Stable Continental Crust 1           4,100        102   
source_model.xml 22     Active Shallow Crust     1           1,339        1,339 
source_model.xml 23     Stable Continental Crust 1           4,100        102   
source_model.xml 24     Active Shallow Crust     1           1,334        1,334 
source_model.xml 25     Stable Continental Crust 1           4,715        117   
source_model.xml 26     Active Shallow Crust     1           1,337        1,337 
source_model.xml 27     Stable Continental Crust 1           4,715        117   
source_model.xml 28     Active Shallow Crust     1           1,339        1,339 
source_model.xml 29     Stable Continental Crust 1           4,715        117   
source_model.xml 30     Active Shallow Crust     1           1,334        1,334 
source_model.xml 31     Stable Continental Crust 1           5,330        133   
source_model.xml 32     Active Shallow Crust     1           1,337        1,337 
source_model.xml 33     Stable Continental Crust 1           5,330        133   
source_model.xml 34     Active Shallow Crust     1           1,339        1,339 
source_model.xml 35     Stable Continental Crust 1           5,330        133   
source_model.xml 36     Active Shallow Crust     1           1,334        1,334 
source_model.xml 37     Stable Continental Crust 1           4,100        102   
source_model.xml 38     Active Shallow Crust     1           1,337        1,337 
source_model.xml 39     Stable Continental Crust 1           4,100        102   
source_model.xml 40     Active Shallow Crust     1           1,339        1,339 
source_model.xml 41     Stable Continental Crust 1           4,100        102   
source_model.xml 42     Active Shallow Crust     1           1,334        1,334 
source_model.xml 43     Stable Continental Crust 1           4,715        117   
source_model.xml 44     Active Shallow Crust     1           1,337        1,337 
source_model.xml 45     Stable Continental Crust 1           4,715        117   
source_model.xml 46     Active Shallow Crust     1           1,339        1,339 
source_model.xml 47     Stable Continental Crust 1           4,715        117   
source_model.xml 48     Active Shallow Crust     1           1,334        1,334 
source_model.xml 49     Stable Continental Crust 1           5,330        133   
source_model.xml 50     Active Shallow Crust     1           1,337        1,337 
source_model.xml 51     Stable Continental Crust 1           5,330        133   
source_model.xml 52     Active Shallow Crust     1           1,339        1,339 
source_model.xml 53     Stable Continental Crust 1           5,330        133   
source_model.xml 54     Active Shallow Crust     1           1,334        1,334 
source_model.xml 55     Stable Continental Crust 1           4,100        102   
source_model.xml 56     Active Shallow Crust     1           1,337        1,337 
source_model.xml 57     Stable Continental Crust 1           4,100        102   
source_model.xml 58     Active Shallow Crust     1           1,339        1,339 
source_model.xml 59     Stable Continental Crust 1           4,100        102   
source_model.xml 60     Active Shallow Crust     1           1,334        1,334 
source_model.xml 61     Stable Continental Crust 1           4,715        117   
source_model.xml 62     Active Shallow Crust     1           1,337        1,337 
source_model.xml 63     Stable Continental Crust 1           4,715        117   
source_model.xml 64     Active Shallow Crust     1           1,339        1,339 
source_model.xml 65     Stable Continental Crust 1           4,715        117   
source_model.xml 66     Active Shallow Crust     1           1,334        1,334 
source_model.xml 67     Stable Continental Crust 1           5,330        133   
source_model.xml 68     Active Shallow Crust     1           1,337        1,337 
source_model.xml 69     Stable Continental Crust 1           5,330        133   
source_model.xml 70     Active Shallow Crust     1           1,339        1,339 
source_model.xml 71     Stable Continental Crust 1           5,330        133   
source_model.xml 72     Active Shallow Crust     1           1,334        1,334 
source_model.xml 73     Stable Continental Crust 1           4,100        102   
source_model.xml 74     Active Shallow Crust     1           1,337        1,337 
source_model.xml 75     Stable Continental Crust 1           4,100        102   
source_model.xml 76     Active Shallow Crust     1           1,339        1,339 
source_model.xml 77     Stable Continental Crust 1           4,100        102   
source_model.xml 78     Active Shallow Crust     1           1,334        1,334 
source_model.xml 79     Stable Continental Crust 1           4,715        117   
source_model.xml 80     Active Shallow Crust     1           1,337        1,337 
source_model.xml 81     Stable Continental Crust 1           4,715        117   
source_model.xml 82     Active Shallow Crust     1           1,339        1,339 
source_model.xml 83     Stable Continental Crust 1           4,715        117   
source_model.xml 84     Active Shallow Crust     1           1,334        1,334 
source_model.xml 85     Stable Continental Crust 1           5,330        133   
source_model.xml 86     Active Shallow Crust     1           1,337        1,337 
source_model.xml 87     Stable Continental Crust 1           5,330        133   
source_model.xml 88     Active Shallow Crust     1           1,339        1,339 
source_model.xml 89     Stable Continental Crust 1           5,330        133   
source_model.xml 90     Active Shallow Crust     1           1,334        1,334 
source_model.xml 91     Stable Continental Crust 1           4,100        102   
source_model.xml 92     Active Shallow Crust     1           1,337        1,337 
source_model.xml 93     Stable Continental Crust 1           4,100        102   
source_model.xml 94     Active Shallow Crust     1           1,339        1,339 
source_model.xml 95     Stable Continental Crust 1           4,100        102   
source_model.xml 96     Active Shallow Crust     1           1,334        1,334 
source_model.xml 97     Stable Continental Crust 1           4,715        117   
source_model.xml 98     Active Shallow Crust     1           1,337        1,337 
source_model.xml 99     Stable Continental Crust 1           4,715        117   
source_model.xml 100    Active Shallow Crust     1           1,339        1,339 
source_model.xml 101    Stable Continental Crust 1           4,715        117   
source_model.xml 102    Active Shallow Crust     1           1,334        1,334 
source_model.xml 103    Stable Continental Crust 1           5,330        133   
source_model.xml 104    Active Shallow Crust     1           1,337        1,337 
source_model.xml 105    Stable Continental Crust 1           5,330        133   
source_model.xml 106    Active Shallow Crust     1           1,339        1,339 
source_model.xml 107    Stable Continental Crust 1           5,330        133   
source_model.xml 108    Active Shallow Crust     1           1,334        1,334 
source_model.xml 109    Stable Continental Crust 1           4,100        102   
source_model.xml 110    Active Shallow Crust     1           1,337        1,337 
source_model.xml 111    Stable Continental Crust 1           4,100        102   
source_model.xml 112    Active Shallow Crust     1           1,339        1,339 
source_model.xml 113    Stable Continental Crust 1           4,100        102   
source_model.xml 114    Active Shallow Crust     1           1,334        1,334 
source_model.xml 115    Stable Continental Crust 1           4,715        117   
source_model.xml 116    Active Shallow Crust     1           1,337        1,337 
source_model.xml 117    Stable Continental Crust 1           4,715        117   
source_model.xml 118    Active Shallow Crust     1           1,339        1,339 
source_model.xml 119    Stable Continental Crust 1           4,715        117   
source_model.xml 120    Active Shallow Crust     1           1,334        1,334 
source_model.xml 121    Stable Continental Crust 1           5,330        133   
source_model.xml 122    Active Shallow Crust     1           1,337        1,337 
source_model.xml 123    Stable Continental Crust 1           5,330        133   
source_model.xml 124    Active Shallow Crust     1           1,339        1,339 
source_model.xml 125    Stable Continental Crust 1           5,330        133   
source_model.xml 126    Active Shallow Crust     1           1,334        1,334 
source_model.xml 127    Stable Continental Crust 1           4,100        102   
source_model.xml 128    Active Shallow Crust     1           1,337        1,337 
source_model.xml 129    Stable Continental Crust 1           4,100        102   
source_model.xml 130    Active Shallow Crust     1           1,339        1,339 
source_model.xml 131    Stable Continental Crust 1           4,100        102   
source_model.xml 132    Active Shallow Crust     1           1,334        1,334 
source_model.xml 133    Stable Continental Crust 1           4,715        117   
source_model.xml 134    Active Shallow Crust     1           1,337        1,337 
source_model.xml 135    Stable Continental Crust 1           4,715        117   
source_model.xml 136    Active Shallow Crust     1           1,339        1,339 
source_model.xml 137    Stable Continental Crust 1           4,715        117   
source_model.xml 138    Active Shallow Crust     1           1,334        1,334 
source_model.xml 139    Stable Continental Crust 1           5,330        133   
source_model.xml 140    Active Shallow Crust     1           1,337        1,337 
source_model.xml 141    Stable Continental Crust 1           5,330        133   
source_model.xml 142    Active Shallow Crust     1           1,339        1,339 
source_model.xml 143    Stable Continental Crust 1           5,330        133   
source_model.xml 144    Active Shallow Crust     1           1,334        1,334 
source_model.xml 145    Stable Continental Crust 1           4,100        102   
source_model.xml 146    Active Shallow Crust     1           1,337        1,337 
source_model.xml 147    Stable Continental Crust 1           4,100        102   
source_model.xml 148    Active Shallow Crust     1           1,339        1,339 
source_model.xml 149    Stable Continental Crust 1           4,100        102   
source_model.xml 150    Active Shallow Crust     1           1,334        1,334 
source_model.xml 151    Stable Continental Crust 1           4,715        117   
source_model.xml 152    Active Shallow Crust     1           1,337        1,337 
source_model.xml 153    Stable Continental Crust 1           4,715        117   
source_model.xml 154    Active Shallow Crust     1           1,339        1,339 
source_model.xml 155    Stable Continental Crust 1           4,715        117   
source_model.xml 156    Active Shallow Crust     1           1,334        1,334 
source_model.xml 157    Stable Continental Crust 1           5,330        133   
source_model.xml 158    Active Shallow Crust     1           1,337        1,337 
source_model.xml 159    Stable Continental Crust 1           5,330        133   
source_model.xml 160    Active Shallow Crust     1           1,339        1,339 
source_model.xml 161    Stable Continental Crust 1           5,330        133   
================ ====== ======================== =========== ============ ======

=============== =======
#TRT models     162    
#sources        162    
#eff_ruptures   490,185
filtered_weight 117,818
=============== =======

Expected data transfer for the sources
--------------------------------------
=========================== ========
Number of tasks to generate 162     
Sent data                   49.96 MB
=========================== ========

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            2         SimpleFaultSource 1,334  1         0.003       0.0        0.0      
86           2         SimpleFaultSource 1,337  1         0.003       0.0        0.0      
88           2         SimpleFaultSource 1,339  1         0.003       0.0        0.0      
2            2         SimpleFaultSource 1,337  1         0.002       0.0        0.0      
22           2         SimpleFaultSource 1,339  1         0.002       0.0        0.0      
16           2         SimpleFaultSource 1,339  1         0.002       0.0        0.0      
138          2         SimpleFaultSource 1,334  1         0.002       0.0        0.0      
150          2         SimpleFaultSource 1,334  1         0.002       0.0        0.0      
58           2         SimpleFaultSource 1,339  1         0.002       0.0        0.0      
14           2         SimpleFaultSource 1,337  1         0.002       0.0        0.0      
64           2         SimpleFaultSource 1,339  1         0.002       0.0        0.0      
4            2         SimpleFaultSource 1,339  1         0.002       0.0        0.0      
136          2         SimpleFaultSource 1,339  1         0.002       0.0        0.0      
66           2         SimpleFaultSource 1,334  1         0.002       0.0        0.0      
76           2         SimpleFaultSource 1,339  1         0.002       0.0        0.0      
160          2         SimpleFaultSource 1,339  1         0.002       0.0        0.0      
134          2         SimpleFaultSource 1,337  1         0.002       0.0        0.0      
50           2         SimpleFaultSource 1,337  1         0.002       0.0        0.0      
56           2         SimpleFaultSource 1,337  1         0.002       0.0        0.0      
70           2         SimpleFaultSource 1,339  1         0.002       0.0        0.0      
============ ========= ================= ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               15        0.0       1     
reading composite source model 9.320     0.0       1     
filtering sources              0.312     0.0       162   
total count_eff_ruptures       0.215     0.012     162   
aggregate curves               0.004     0.0       162   
store source_info              3.850E-04 0.0       1     
reading site collection        5.293E-05 0.0       1     
============================== ========= ========= ======