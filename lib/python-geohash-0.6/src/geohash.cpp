#include <stdio.h>
#include <math.h>
#include <string.h>
#include "geohash.h"

#if defined(_MSC_VER) && (_MSC_VER <= 1500)
typedef unsigned __int8 uint8_t;
typedef unsigned __int16 uint16_t;
typedef unsigned __int64 uint64_t;
#define UINT64_C(C) ((uint64_t) C ## ULL)
#else
#define __STDC_CONSTANT_MACROS 1
#include <stdint.h>
#endif

#ifdef _MSC_VER
// http://msdn.microsoft.com/en-us/library/b0084kay(VS.80).aspx
#if defined(_M_IX86) || defined(_M_IA64) || defined(_M_X64)
# define __LITTLE_ENDIAN__
#endif
#else /* _MSC_VER */
#include <sys/param.h>
#if !defined(__LITTLE_ENDIAN__) && !defined(__BIG_ENDIAN__) /* MacOS X style */
#ifdef __BYTE_ORDER /* Linux style */
# if __BYTE_ORDER == __LITTLE_ENDIAN
#  define __LITTLE_ENDIAN__
# endif
# if __BYTE_ORDER == __BIG_ENDIAN
#  define __BIG_ENDIAN__
# endif
#endif
#ifdef BYTE_ORDER /* MinGW style */
# if BYTE_ORDER == LITTLE_ENDIAN
#  define __LITTLE_ENDIAN__
# endif
# if BYTE_ORDER == BIG_ENDIAN
#  define __BIG_ENDIAN__
# endif
#endif
#endif
#endif /* _MSC_VER */

#if !defined(__LITTLE_ENDIAN__) && !defined(__BIG_ENDIAN__)
/* I don't have __PDP_ENDIAN machine. Please let me know if you have one. */
#define __UNSUPPORTED_ENDIAN__
#endif

#ifdef __LITTLE_ENDIAN__
#define B7 7
#define B6 6
#define B5 5
#define B4 4
#define B3 3
#define B2 2
#define B1 1
#define B0 0
#endif

#ifdef __BIG_ENDIAN__
#define B7 0
#define B6 1
#define B5 2
#define B4 3
#define B3 4
#define B2 5
#define B1 6
#define B0 7
#endif


#ifdef PYTHON_MODULE
#include <Python.h>
static PyObject *py_geohash_encode(PyObject *self, PyObject *args) {
	double latitude;
	double longitude;
	char hashcode[28];
	int ret = GEOHASH_OK;
	
	if(!PyArg_ParseTuple(args, "dd", &latitude, &longitude)) return NULL;
	
	if((ret=geohash_encode(latitude,longitude,hashcode,28))!=GEOHASH_OK){
		if(ret==GEOHASH_NOTSUPPORTED) PyErr_SetString(PyExc_EnvironmentError, "unknown endian");
		return NULL;
	}
	return Py_BuildValue("s",hashcode);
}
static PyObject *py_geohash_decode(PyObject *self, PyObject *args) {
	double latitude;
	double longitude;
	char *hashcode;
	int codelen=0;
	int ret = GEOHASH_OK;
	
	if(!PyArg_ParseTuple(args, "s", &hashcode)) return NULL;
	
	codelen = strlen(hashcode);
	if((ret=geohash_decode(hashcode,codelen,&latitude,&longitude))!=GEOHASH_OK){
		PyErr_SetString(PyExc_ValueError,"geohash code is [0123456789bcdefghjkmnpqrstuvwxyz]+");
		return NULL;
	}
	return Py_BuildValue("(ddii)",latitude,longitude, codelen/2*5+codelen%2*2, codelen/2*5+codelen%2*3);
}

static PyObject *py_geohash_neighbors(PyObject *self, PyObject *args) {
	static const unsigned char mapA[128] = {
		  '@',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		    0,    1,    2,    3,    4,    5,    6,    7,
		    8,    9,  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|', 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
		 0x10,  '|', 0x11, 0x12,  '|', 0x13, 0x14,  '|',
		 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C,
		 0x1D, 0x1E, 0x1F,  '|',  '|',  '|',  '|',  '|',
		  '|',  '|', 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
		 0x10,  '|', 0x11, 0x12,  '|', 0x13, 0x14,  '|',
		 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C,
		 0x1D, 0x1E, 0x1F,  '|',  '|',  '|',  '|',  '|',
	};
	static const char rmap[33]="0123456789bcdefghjkmnpqrstuvwxyz";
	uint64_t lat, lon;
	char *hashcode;
	if(!PyArg_ParseTuple(args, "s", &hashcode)) return NULL;
	
	int length = strlen(hashcode);
	if(length>24){ length=24; } // round if the hashcode is too long (over 64bit)
	lat=lon=0;
	int cshift=0;
	while(cshift<length){
		unsigned char o1 = mapA[(unsigned char)hashcode[cshift]];
		if(o1=='@'){ break; }
		if(o1=='|'){
			PyErr_SetString(PyExc_ValueError,"geohash code is [0123456789bcdefghjkmnpqrstuvwxyz]+");
			return NULL;
		}
		if(cshift%2==0){
			lon = (lon<<3) | ((o1&0x10)>>2) | ((o1&0x04)>>1) | (o1&0x01);
			lat = (lat<<2) | ((o1&0x08)>>2) | ((o1&0x02)>>1);
		}else{
			lon = (lon<<2) | ((o1&0x08)>>2) | ((o1&0x02)>>1);
			lat = (lat<<3) | ((o1&0x10)>>2) | ((o1&0x04)>>1) | (o1&0x01);
		}
		cshift++;
	}
	
	char* buffer = (char*)malloc(8*(length+1)*sizeof(char));
	if(buffer==NULL){
		PyErr_NoMemory();
		return NULL;
	}
	int al=-1;
	int au=2;
	if(lat==0){
		al=0; au=2;
	}else if(lat+1==(UINT64_C(1)<<(length/2*5+length%2*2))){
		al=-1; au=1;
	}
	int blen=length+1; // block length
	int aoff=0;
	int a,o;
	for(a=al;a<au;a++){
		for(o=-1;o<2;o++){
			if(a==0 && o==0) continue;
			uint64_t ta = lat+a;
			uint64_t to = lon+o;
			buffer[blen*aoff+length]='\0';
			int cpos = length-1;
			while(cpos>=0){
				unsigned char z;
				if(cpos%2==0){
					z = ((to&4)<<2)|((to&2)<<1)|(to&1)|((ta&2)<<2)|((ta&1)<<1);
					buffer[blen*aoff+cpos]=rmap[z];
					ta=ta>>2;
					to=to>>3;
				}else{
					z = ((ta&4)<<2)|((ta&2)<<1)|(ta&1)|((to&2)<<2)|((to&1)<<1);
					buffer[blen*aoff+cpos]=rmap[z];
					ta=ta>>3;
					to=to>>2;
				}
				cpos--;
			}
			aoff++;
		}
	}
	PyObject *ret;
	if(lat==0){
		ret= Py_BuildValue("[sssss]",&buffer[0],&buffer[blen],&buffer[blen*2],&buffer[blen*3],&buffer[blen*4]);
	}else if(lat+1==(UINT64_C(1)<<(cshift/2*5+cshift%2*2))){
		ret= Py_BuildValue("[sssss]",&buffer[0],&buffer[blen],&buffer[blen*2],&buffer[blen*3],&buffer[blen*4]);
	}else{
		ret= Py_BuildValue("[ssssssss]",&buffer[0],&buffer[blen],&buffer[blen*2],&buffer[blen*3],
			&buffer[blen*4],&buffer[blen*5],&buffer[blen*6],&buffer[blen*7]);
	}
	free(buffer);
	return ret;
}

static PyMethodDef GeohashMethods[] = {
	{"encode", py_geohash_encode, METH_VARARGS, "geohash encoding."},
	{"decode", py_geohash_decode, METH_VARARGS, "geohash decoding."},
	{"neighbors", py_geohash_neighbors, METH_VARARGS, "geohash neighbor codes",},
	{NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC init_geohash(void){
	(void)Py_InitModule("_geohash", GeohashMethods);
};
#endif /* PYTHON_MODULE */

static inline uint64_t interleave(uint8_t upper, uint8_t lower){
	static const uint16_t map[255] = {
		UINT64_C(0x0000), UINT64_C(0x0001), UINT64_C(0x0004), UINT64_C(0x0005), UINT64_C(0x0010), UINT64_C(0x0011), 
		UINT64_C(0x0014), UINT64_C(0x0015), UINT64_C(0x0040), UINT64_C(0x0041), UINT64_C(0x0044), UINT64_C(0x0045), 
		UINT64_C(0x0050), UINT64_C(0x0051), UINT64_C(0x0054), UINT64_C(0x0055), UINT64_C(0x0100), UINT64_C(0x0101), 
		UINT64_C(0x0104), UINT64_C(0x0105), UINT64_C(0x0110), UINT64_C(0x0111), UINT64_C(0x0114), UINT64_C(0x0115), 
		UINT64_C(0x0140), UINT64_C(0x0141), UINT64_C(0x0144), UINT64_C(0x0145), UINT64_C(0x0150), UINT64_C(0x0151), 
		UINT64_C(0x0154), UINT64_C(0x0155), UINT64_C(0x0400), UINT64_C(0x0401), UINT64_C(0x0404), UINT64_C(0x0405), 
		UINT64_C(0x0410), UINT64_C(0x0411), UINT64_C(0x0414), UINT64_C(0x0415), UINT64_C(0x0440), UINT64_C(0x0441), 
		UINT64_C(0x0444), UINT64_C(0x0445), UINT64_C(0x0450), UINT64_C(0x0451), UINT64_C(0x0454), UINT64_C(0x0455), 
		UINT64_C(0x0500), UINT64_C(0x0501), UINT64_C(0x0504), UINT64_C(0x0505), UINT64_C(0x0510), UINT64_C(0x0511), 
		UINT64_C(0x0514), UINT64_C(0x0515), UINT64_C(0x0540), UINT64_C(0x0541), UINT64_C(0x0544), UINT64_C(0x0545), 
		UINT64_C(0x0550), UINT64_C(0x0551), UINT64_C(0x0554), UINT64_C(0x0555), UINT64_C(0x1000), UINT64_C(0x1001), 
		UINT64_C(0x1004), UINT64_C(0x1005), UINT64_C(0x1010), UINT64_C(0x1011), UINT64_C(0x1014), UINT64_C(0x1015), 
		UINT64_C(0x1040), UINT64_C(0x1041), UINT64_C(0x1044), UINT64_C(0x1045), UINT64_C(0x1050), UINT64_C(0x1051), 
		UINT64_C(0x1054), UINT64_C(0x1055), UINT64_C(0x1100), UINT64_C(0x1101), UINT64_C(0x1104), UINT64_C(0x1105), 
		UINT64_C(0x1110), UINT64_C(0x1111), UINT64_C(0x1114), UINT64_C(0x1115), UINT64_C(0x1140), UINT64_C(0x1141), 
		UINT64_C(0x1144), UINT64_C(0x1145), UINT64_C(0x1150), UINT64_C(0x1151), UINT64_C(0x1154), UINT64_C(0x1155), 
		UINT64_C(0x1400), UINT64_C(0x1401), UINT64_C(0x1404), UINT64_C(0x1405), UINT64_C(0x1410), UINT64_C(0x1411), 
		UINT64_C(0x1414), UINT64_C(0x1415), UINT64_C(0x1440), UINT64_C(0x1441), UINT64_C(0x1444), UINT64_C(0x1445), 
		UINT64_C(0x1450), UINT64_C(0x1451), UINT64_C(0x1454), UINT64_C(0x1455), UINT64_C(0x1500), UINT64_C(0x1501), 
		UINT64_C(0x1504), UINT64_C(0x1505), UINT64_C(0x1510), UINT64_C(0x1511), UINT64_C(0x1514), UINT64_C(0x1515), 
		UINT64_C(0x1540), UINT64_C(0x1541), UINT64_C(0x1544), UINT64_C(0x1545), UINT64_C(0x1550), UINT64_C(0x1551), 
		UINT64_C(0x1554), UINT64_C(0x1555), UINT64_C(0x4000), UINT64_C(0x4001), UINT64_C(0x4004), UINT64_C(0x4005), 
		UINT64_C(0x4010), UINT64_C(0x4011), UINT64_C(0x4014), UINT64_C(0x4015), UINT64_C(0x4040), UINT64_C(0x4041), 
		UINT64_C(0x4044), UINT64_C(0x4045), UINT64_C(0x4050), UINT64_C(0x4051), UINT64_C(0x4054), UINT64_C(0x4055), 
		UINT64_C(0x4100), UINT64_C(0x4101), UINT64_C(0x4104), UINT64_C(0x4105), UINT64_C(0x4110), UINT64_C(0x4111), 
		UINT64_C(0x4114), UINT64_C(0x4115), UINT64_C(0x4140), UINT64_C(0x4141), UINT64_C(0x4144), UINT64_C(0x4145), 
		UINT64_C(0x4150), UINT64_C(0x4151), UINT64_C(0x4154), UINT64_C(0x4155), UINT64_C(0x4400), UINT64_C(0x4401), 
		UINT64_C(0x4404), UINT64_C(0x4405), UINT64_C(0x4410), UINT64_C(0x4411), UINT64_C(0x4414), UINT64_C(0x4415), 
		UINT64_C(0x4440), UINT64_C(0x4441), UINT64_C(0x4444), UINT64_C(0x4445), UINT64_C(0x4450), UINT64_C(0x4451), 
		UINT64_C(0x4454), UINT64_C(0x4455), UINT64_C(0x4500), UINT64_C(0x4501), UINT64_C(0x4504), UINT64_C(0x4505), 
		UINT64_C(0x4510), UINT64_C(0x4511), UINT64_C(0x4514), UINT64_C(0x4515), UINT64_C(0x4540), UINT64_C(0x4541), 
		UINT64_C(0x4544), UINT64_C(0x4545), UINT64_C(0x4550), UINT64_C(0x4551), UINT64_C(0x4554), UINT64_C(0x4555), 
		UINT64_C(0x5000), UINT64_C(0x5001), UINT64_C(0x5004), UINT64_C(0x5005), UINT64_C(0x5010), UINT64_C(0x5011), 
		UINT64_C(0x5014), UINT64_C(0x5015), UINT64_C(0x5040), UINT64_C(0x5041), UINT64_C(0x5044), UINT64_C(0x5045), 
		UINT64_C(0x5050), UINT64_C(0x5051), UINT64_C(0x5054), UINT64_C(0x5055), UINT64_C(0x5100), UINT64_C(0x5101), 
		UINT64_C(0x5104), UINT64_C(0x5105), UINT64_C(0x5110), UINT64_C(0x5111), UINT64_C(0x5114), UINT64_C(0x5115), 
		UINT64_C(0x5140), UINT64_C(0x5141), UINT64_C(0x5144), UINT64_C(0x5145), UINT64_C(0x5150), UINT64_C(0x5151), 
		UINT64_C(0x5154), UINT64_C(0x5155), UINT64_C(0x5400), UINT64_C(0x5401), UINT64_C(0x5404), UINT64_C(0x5405), 
		UINT64_C(0x5410), UINT64_C(0x5411), UINT64_C(0x5414), UINT64_C(0x5415), UINT64_C(0x5440), UINT64_C(0x5441), 
		UINT64_C(0x5444), UINT64_C(0x5445), UINT64_C(0x5450), UINT64_C(0x5451), UINT64_C(0x5454), UINT64_C(0x5455), 
		UINT64_C(0x5500), UINT64_C(0x5501), UINT64_C(0x5504), UINT64_C(0x5505), UINT64_C(0x5510), UINT64_C(0x5511), 
		UINT64_C(0x5514), UINT64_C(0x5515), UINT64_C(0x5540), UINT64_C(0x5541), UINT64_C(0x5544), UINT64_C(0x5545), 
		UINT64_C(0x5550), UINT64_C(0x5551), UINT64_C(0x5554)
	};
	return (map[upper]<<1)+map[lower];
}

/*
  latitude must be in [-90.0, 90.0) and longitude must be in [-180.0 180.0)
*/
int geohash_encode(double latitude, double longitude, char* r, size_t capacity){
	static const char* map="0123456789bcdefghjkmnpqrstuvwxyz";
	union {
		double d; // assuming IEEE 754-1985 binary64. This might not be true on some CPU (I don't know which).
		// formally, we should use unsigned char for type-punning (see C99 ISO/IEC 9899:201x spec 6.2.6)
		uint64_t i64;
	} lat, lon;
	unsigned short lat_exp, lon_exp;
	char lr[27];
	
#ifdef __UNSUPPORTED_ENDIAN__
	if(capacity>0){ r[0]='\0'; }
	return GEOHASH_NOTSUPPORTED;
#endif
	
	lat.d = latitude/180.0;
	lon.d = longitude/360.0;
	
	lat_exp = (lat.i64>>52) & UINT64_C(0x7FF);
	if(lat.d!=0.0){
		lat.i64 = (lat.i64 & UINT64_C(0xFFFFFFFFFFFFF)) | UINT64_C(0x10000000000000);
	}
	lon_exp = (lon.i64>>52) & UINT64_C(0x7FF);
	if(lon.d!=0.0){
		lon.i64 = (lon.i64 & UINT64_C(0xFFFFFFFFFFFFF)) | UINT64_C(0x10000000000000);
	}
	
	if(lat_exp<1011){
		lat.i64=lat.i64>>(1011-lat_exp);
	}else{
		lat.i64=lat.i64<<(lat_exp-1011);
	}
	if(lon_exp<1011){
		lon.i64=lon.i64>>(1011-lon_exp);
	}else{
		lon.i64=lon.i64<<(lon_exp-1011);
	}
	
	if(latitude>0.0){
		lat.i64 = UINT64_C(0x8000000000000000) + lat.i64;
	}else{
		lat.i64 = UINT64_C(0x8000000000000000) - lat.i64;
	}
	if(longitude>0.0){
		lon.i64 = UINT64_C(0x8000000000000000) + lon.i64;
	}else{
		lon.i64 = UINT64_C(0x8000000000000000) - lon.i64;
	}
	
	uint64_t idx0,idx1;
	idx0 = idx1 = 0;
	idx1 |= interleave(lon.i64>>56, lat.i64>>56)<<48;
	idx1 |= interleave(lon.i64>>48, lat.i64>>48)<<32;
	idx1 |= interleave(lon.i64>>40, lat.i64>>40)<<16;
	idx1 |= interleave(lon.i64>>32, lat.i64>>32);
	idx0 |= interleave(lon.i64>>24, lat.i64>>24)<<48;
	idx0 |= interleave(lon.i64>>16, lat.i64>>16)<<32;
	idx0 |= interleave(lon.i64>>8, lat.i64>>8)<<16;
	idx0 |= interleave(lon.i64, lat.i64);
	lr[0] = map[(idx1>>59)&0x1F];
	lr[1] = map[(idx1>>54)&0x1F];
	lr[2] = map[(idx1>>49)&0x1F];
	lr[3] = map[(idx1>>44)&0x1F];
	lr[4] = map[(idx1>>39)&0x1F];
	lr[5] = map[(idx1>>34)&0x1F];
	lr[6] = map[(idx1>>29)&0x1F];
	lr[7] = map[(idx1>>24)&0x1F];
	lr[8] = map[(idx1>>19)&0x1F];
	lr[9] = map[(idx1>>14)&0x1F];
	lr[10] = map[(idx1>>9)&0x1F];
	lr[11] = map[(idx1>>4)&0x1F];
	lr[12] = map[((idx1<<1)&0x1E)|(idx0>>63)];
	lr[13] = map[(idx0>>58)&0x1F];
	lr[14] = map[(idx0>>53)&0x1F];
	lr[15] = map[(idx0>>48)&0x1F];
	lr[16] = map[(idx0>>43)&0x1F];
	lr[17] = map[(idx0>>38)&0x1F];
	lr[18] = map[(idx0>>33)&0x1F];
	lr[19] = map[(idx0>>28)&0x1F];
	lr[20] = map[(idx0>>23)&0x1F];
	lr[21] = map[(idx0>>18)&0x1F];
	lr[22] = map[(idx0>>13)&0x1F];
	lr[23] = map[(idx0>>8)&0x1F];
	lr[24] = map[(idx0>>3)&0x1F];
	lr[25] = map[(idx0<<2)&0x1F];
	lr[26] = '\0';
	if(0<capacity){
		if(capacity<27){
			memcpy(r, (const char*)lr, capacity-1);
			r[capacity-1]='\0';
		}else{
			memcpy(r, (const char*)lr, 27);
		}
	}
	return GEOHASH_OK;
}

/*
   (latitude, longitude) will be that of south west point.
*/
int geohash_decode(char* r, size_t length, double *latitude, double *longitude){
	static const unsigned char map[128] = {
		  '@',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|',  '|',  '|',  '|',  '|',  '|',  '|',
		    0,    1,    2,    3,    4,    5,    6,    7,
		    8,    9,  '|',  '|',  '|',  '|',  '|',  '|',
		  '|',  '|', 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
		 0x10,  '|', 0x11, 0x12,  '|', 0x13, 0x14,  '|',
		 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C,
		 0x1D, 0x1E, 0x1F,  '|',  '|',  '|',  '|',  '|',
		  '|',  '|', 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
		 0x10,  '|', 0x11, 0x12,  '|', 0x13, 0x14,  '|',
		 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C,
		 0x1D, 0x1E, 0x1F,  '|',  '|',  '|',  '|',  '|',
	};
	unsigned int cshift=0;
	if(length>25){ length=25; } // round if the hashcode is too long (over 64bit)
	union {
		double d; // assuming IEEE 754-1985 binary64. This might not be true on some CPU (I don't know which).
		unsigned char s[8];
		// formally, we should use unsigned char for type-punning (see C99 ISO/IEC 9899:201x spec 6.2.6)
		uint64_t i64;
	} lat, lon;
	lat.i64 = lon.i64 = 0;
	while(cshift<length){
		unsigned char o1 = map[(unsigned char)r[cshift]];
		if(o1=='@'){ break; }
		if(o1=='|'){
			return GEOHASH_INVALIDCODE;
		}
		if(cshift%2==0){
			lon.i64 = (lon.i64<<3) | ((o1&0x10)>>2) | ((o1&0x04)>>1) | (o1&0x01);
			lat.i64 = (lat.i64<<2) | ((o1&0x08)>>2) | ((o1&0x02)>>1);
		}else{
			lon.i64 = (lon.i64<<2) | ((o1&0x08)>>2) | ((o1&0x02)>>1);
			lat.i64 = (lat.i64<<3) | ((o1&0x10)>>2) | ((o1&0x04)>>1) | (o1&0x01);
		}
		cshift++;
	}
	if(cshift==0){
		// cshift=1; // no input equals to '0'
		// but we do know the result.
		*latitude = -90.0;
		*longitude = -180.0;
		return GEOHASH_OK;
	}
	
	int lat_neg=0,lon_neg=0;
	uint64_t lat_h,lon_h;
	lat_h=UINT64_C(1)<<(5*(cshift/2) + 2*(cshift%2)-1);
	lon_h=UINT64_C(1)<<(5*(cshift/2) + 3*(cshift%2)-1);
	
	if(lat.i64>=lat_h){
		lat.i64=lat.i64-lat_h;
	}else{
		lat.i64=lat_h-lat.i64;
		lat_neg=1;
	}
	if(lon.i64>=lon_h){
		lon.i64=lon.i64-lon_h;
	}else{
		lon.i64=lon_h-lon.i64;
		lon_neg=1;
	}
	
	// rounding to double representation
	int i,lat_i=-1,lon_i=-1;
	for(i=0;i<64;i++){
		if(lat.i64>>i){ lat_i=i; }
		if(lon.i64>>i){ lon_i=i; }
	}
	
	if(lat_i==-1){
		lat_i = 0;
	}else{
		if(lat_i>52){
			lat.i64=lat.i64>>(lat_i-52);
		}else{
			lat.i64=lat.i64<<(52-lat_i);
		}
		lat_i = 1023 + lat_i - 5*(cshift/2) - 2*(cshift%2);
	}
	if(lon_i==-1){
		lon_i = 0;
	}else{
		if(lon_i>52){
			lon.i64=lon.i64>>(lon_i-52);
		}else{
			lon.i64=lon.i64<<(52-lon_i);
		}
		lon_i = 1023 + lon_i - 5*(cshift/2) - 3*(cshift%2);
	}
	
	lat.s[B7]=(lat_neg<<7)|((lat_i>>4)&0x7F);
	lon.s[B7]=(lon_neg<<7)|((lon_i>>4)&0x7F);
	lat.s[B6]=((lat_i<<4)&0xF0)|(lat.s[B6]&0x0F);
	lon.s[B6]=((lon_i<<4)&0xF0)|(lon.s[B6]&0x0F);
	
	*latitude = 180.0*lat.d;
	*longitude = 360.0*lon.d;
	return GEOHASH_OK;
}
