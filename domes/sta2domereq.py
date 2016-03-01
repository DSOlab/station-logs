#! /usr/bin/python

import sys
import bernutils.bsta2 as bs

def get_llh(station, filen):
    with open(filen, 'r') as fin:
        for line in fin.readlines():
            l = line.split()
            if l[0] == station:
                lat = float(l[1])
                lon = float(l[2])
                hgt = float(l[3])
                lat_deg = int(lat)
                lat_min = int((lat - lat_deg)*60.0e0)
                lon_deg = int(lon)
                lon_min = int((lon - lon_deg)*60.0e0)
                break
    lat_str = '{0:+02d}.{1:02d}'.format(lat_deg, lat_min)
    lon_str = '{0:+03d}.{1:02d}'.format(lon_deg, lon_min)
    hgt_str = '{0:5.1f}'.format(hgt)
    return lat_str, lon_str, hgt_str

sta_file     = sys.argv[1]
station_name = sys.argv[2].upper()

bsta = bs.BernSta(sta_file)

t1_dict = bsta.__match_type_001__([station_name])
t2_dict = bsta.__match_type_002__(t1_dict)

if len(t2_dict) > 1:
    print >> sys.stderr, '[ERROR] More than one records for station', station_name
    sys.exit(1)
elif len(t2_dict) < 1:
    print >> sys.stderr, '[ERROR] Station',station_name,'not matched!'
    sys.exit(1)

sta_t2    = t2_dict[station_name][0]
site_name = ' '.join(sta_t2['description'].split()[0:-1])
country   = 'Greece'
sta_id    = station_name
plate     = 'EURA'
lat, lon, hgt = get_llh(station_name, 'gps-stations-seismo-flh.txt')
technique = 'GNSS'
install_d = sta_t2['start'].strftime('%Y-%m-%d')

print """
DOMES INFORMATION FORM

 1. Request from (full name) : 

 2. Site Name                : {0:<20s}
 3. Country                  : {1:<20s}
 4. Point Description        :
    Support description      :
    Picture                  : see guidelines

 5. DOMES Number             :  
 6. Local Number             :
 7. 4-Char Code              : {2:4s}

 8. Approximate Position
    Latitude (deg min)       : {3:<10s}
    Longitude (deg min)      : {4:<10s}
    Elevation (m)            : {5:<10s}
    Tectonic plate           : {6:<10s}

 9. Instrument               : {7:<10s}
10. Date of Installation     : {8:<10s}

11. Operation Contact Name   : Philip England
    Agency                   : Centre for Observation and Modelling of Earthquakes, Volcanoes and Tectonics (COMET)
    E-mail                   : philip.england@earth.ox.ac.uk

12. Site Contact Name        : Demitris Paradissis
    Agency                   : National Technical University of Athens
    E-mail                   : dempar@central.ntua.gr
""".format(site_name, country, station_name, lat, lon, hgt, plate, technique, install_d)

sys.exit(0)
