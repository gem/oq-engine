#include <stdio.h>
#include "geohash.h"

int main(int argc,char* argv[]){
	char r[20];
	double lat,lon;
	int res;
	if((res=geohash_encode(35.0, 135.0, r, 20))==GEOHASH_OK){
		printf("%s\n",r);
	}else{
		printf("error with %d\n",res);
	}
	if((res=geohash_decode(r,23,&lat,&lon))==GEOHASH_OK){
		printf("%f %f\n",lat,lon);
	}else{
		printf("error with %d\n",res);
	}
}
