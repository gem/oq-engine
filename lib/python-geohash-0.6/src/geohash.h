#ifdef __cplusplus
extern "C" {
#endif

enum {
	GEOHASH_OK,
	GEOHASH_NOTSUPPORTED,
	GEOHASH_INVALIDCODE,
};

int geohash_encode(double latitude, double longitude, char* r, size_t capacity);
int geohash_decode(char* r, size_t length, double *latitude, double *longitude);

#ifdef __cplusplus
}
#endif


/*
int main(int argc,char* argv[]){
	char r[23];
	double lat,lon;
	if(geohash_encode(35.0, 135.0, r, 23)==GEOHASH_OK){
		printf("%s\n",r);
	}
	if(geohash_decode(r,23,&lat,&lon)==GEOHASH_OK){
		printf("%f %f\n",lat,lon);
	}
}
*/
