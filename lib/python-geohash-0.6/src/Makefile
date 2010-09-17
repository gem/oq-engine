CC	= gcc
CXX	= g++
CFLAGS	= -O3
CXXFLAGS	=
TARGET	= sample
OBJS	= geohash_sample.o geohash.o

all:	$(TARGET)
$(TARGET):	$(OBJS)
	$(CXX) -o $@ $(OBJS)
clean:
	-rm -f $(TARGET) $(OBJS)
.c.o:
	$(CC) $(CFLAGS) -c $<
.cpp.o:
	$(CXX) $(CXXFLAGS) -c $<
