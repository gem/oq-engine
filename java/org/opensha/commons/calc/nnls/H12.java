/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.calc.nnls;


import org.netlib.util.doubleW;

class H12
{
	static double cl = 0.0D;
	static double sm = 0.0D;
	static double sm1 = 0.0D;
	static double clinv = 0.0D;
	static double b = 0.0D;
	static int mdim = 0;
	static int i1 = 0;
	static int i2 = 0;
	static int i3 = 0;
	static int i4 = 0;
	static int i = 0;
	static int j = 0;
	static int incr = 0;
	static int temp_i;
	static int temp_j;
	static double temp;
	H12()
	{
	}
//	C$$$$$ CALLS NO OTHER ROUTINES 
//	C  CONSTRUCTION AND APPLICATION OF HOUSEHOLDER TRANSFORMATION FOR
//	C  MODIFIED FROM  H12  IN LAWSON+HANSEN - SOLVING LEAST SQUARES 
//	C  - PRENTICE-HALL 1974 (PP308,309).  DOUBLE PRECISION THROUGHOUT
	public static final void h12(int k, int l, int j1, int k1, double ad[], int l1, int j2, doubleW doublew, 
			double ad1[], int k2, int l2, int j3, int k3)
	{
		label0:
		{
		label1:
		{
		int l3 = (l - 1) * j2 + l1;
		if(0 >= l || l >= j1 || j1 > k1)
			break label0;
		cl = Math.abs(ad[l3]);
		if(k != 2)
		{
			j = j1;
			for(temp_j = (j - 1) * j2 + l1; j <= k1; temp_j += j2)
			{
				cl = Math.max(Math.abs(ad[temp_j]), cl);
				j++;
			}

			if(cl <= 0.0D)
				break label1;
			clinv = 1.0D / cl;
			temp = ad[l3] * clinv;
			sm = temp * temp;
			j = j1;
			for(temp_j = (j - 1) * j2 + l1; j <= k1; temp_j += j2)
			{
				temp = ad[temp_j] * clinv;
				sm += temp * temp;
				j++;
			}

			sm1 = sm;
			cl = Math.sqrt(sm1) * cl;
			if(ad[l3] > 0.0D)
				cl = -cl;
			doublew.val = ad[l3] - cl;
			ad[l3] = cl;
		} else
		{
			if(cl <= 0.0D)
				break label1;
		}
		if(k3 <= 0)
			break label0;
		b = doublew.val * ad[l3];
		if(b < 0.0D)
		{
			b = 1.0D / b;
			i2 = (1 - j3) + l2 * (l - 1);
			incr = l2 * (j1 - l);
			for(j = 1; j <= k3; j++)
			{
				i2 += j3;
				i3 = i2 + incr;
				i4 = i3;
				sm = ad1[(i2 - 1) + k2] * doublew.val;
				for(i = j1; i <= k1; i++)
				{
					sm = ad1[(i3 - 1) + k2] * ad[(i - 1) * j2 + l1] + sm;
					i3 += l2;
				}

				if(sm != 0.0D)
				{
					sm *= b;
					ad1[(i2 - 1) + k2] = sm * doublew.val + ad1[(i2 - 1) + k2];
					i = j1;
					for(temp_i = (i - 1) * j2 + l1; i <= k1; temp_i += j2)
					{
						ad1[(i4 - 1) + k2] = sm * ad[temp_i] + ad1[(i4 - 1) + k2];
						i4 += l2;
						i++;
					}

				}
			}

		}
		}
		}
	}


}

