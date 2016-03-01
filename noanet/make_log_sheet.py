#! /usr/bin/python

import sys
import datetime
import MySQLdb
import re

DB_HOST="147.102.110.73"
DB_USER="xanthos"
DB_PASS="koko1"
DB_NAME="procsta"
STATUS = 0
ERR_MSG=""

station = sys.argv[1]
sta52f  = sys.argv[2]
rinex   = None
if len(sys.argv) > 3: rinex = sys.argv[3]

def get_rnx_info(station, rnx_file):
    rnx_dict = {}
    with open(rnx_file, 'r') as fin:
        line = fin.readline()
        while line and not re.match(r"END OF HEADER", line):
            if line[60:].rstrip() == "MARKER NAME":
                rnx_dict["name"] = line.split()[0]
            if line[60:].rstrip() == "MARKER NUMBER": rnx_dict["number"] = line[0]
            if line[60:].rstrip() == "REC # / TYPE / VERS":
                rnx_dict["rec_number"] = line[0:20].strip()
                rnx_dict["rec_type"]   = line[20:40].strip()
                rnx_dict["rec_firmw"]  = line[40:60].strip()
            if line[60:].rstrip() == "ANT # / TYPE":
                rnx_dict["ant_number"] = line[0:20].strip()
                rnx_dict["ant_type"]   = line[20:40].strip()
            line = fin.readline()
    if station.upper() != rnx_dict["name"].upper():
        print "## ----------- WARNINGS ---------------"
        print "## You sure you got the right rinex? Names don;t match!"
        print "## Got",station.upper(),"vs",rnx_dict["name"].upper()
        print "## ------------------------------------"
    return rnx_dict


def get_db_info( station ):
    """ Given the station name (DSO) ask the database for all the info
        we have.
    """
    try:
        db  = MySQLdb.connect(
                host   = DB_HOST,
                user   = DB_USER,
                passwd = DB_PASS,
                db     = DB_NAME
            )
        cur = db.cursor()
        ## ok, connected to db; now start quering for each station
        QUERY='SELECT station.station_id, station.mark_name_DSO, stacode.mark_name_OFF, stacode.station_name, ftprnx.dc_name, ftprnx.protocol, ftprnx.url_domain, ftprnx.pth2rnx30s, ftprnx.pth2rnx01s, ftprnx.ftp_usname, ftprnx.ftp_passwd, network.network_name, dataperiod.periodstart, dataperiod.periodstop, station.ecef_X, station.ecef_Y, station.ecef_Z, station.longitude_east, station.latitude_north, station.ellipsoidal_height FROM station JOIN stacode ON station.stacode_id=stacode.stacode_id JOIN dataperiod ON station.station_id=dataperiod.station_id JOIN ftprnx ON dataperiod.ftprnx_id=ftprnx.ftprnx_id JOIN  sta2nets ON sta2nets.station_id=station.station_id JOIN network ON network.network_id=sta2nets.network_id WHERE station.mark_name_DSO="%s";'%station
        cur.execute( QUERY )
        try:
            SENTENCE = cur.fetchall()
            # answer must only have one raw
            if len(SENTENCE) > 1:
                ## station belongs to more than one networks; see bug #13
                print '## [WARNING] station \"%s\" belongs to more than one networks.'%station
                add_sta = True
                ref_line = SENTENCE[0]
                for line in SENTENCE[1:]:
                    for idx, field in enumerate( ref_line[0:10] ):
                        if field != line[idx]:
                            add_sta = False
                            print '[ERROR] Station \"%s\" belongs to more than one networks but independent fields don\'t match!'%station
                            STATUS = 4
                if add_sta is True :
                    return SENTENCE[0]
            elif len(SENTENCE) == 0:
                print '[ERROR] Cannot match station \"%s\" in the database.'%station
                STATUS = 3
            else:
                return SENTENCE[0]
        except:
            print '[ERROR] No matching station name in database for \"%s\".'%station
            ERR_MSG = sys.exc_info()[0]
            STATUS = 2
    except:
        ERR_MSG = sys.exc_info()[0]
        print '[ERROR] Failed connecting to the database'
        STATUS = 1

    if STATUS > 0:
        print >> sys.stderr, ERR_MSG, "STATUS =",STATUS
        raise
    else:
        return SENTENCE[0]

def get_sta_info( station, sta_file ):
    """ Given a station name and a Bernese 52 station information file,
        extract the station information.
    """
    type2_records = []
    with open(sta_file, 'r') as fin:
        for i in range(0,20): line = fin.readline()
        l = line.split()
        while line:
            if len(l)>2 and l[0] == "TYPE" and l[1] == "002:":
                break
            line = fin.readline()
            l    = line.split()
        if not line:
            raise RuntimeError
        for i in range(0,5): line = fin.readline()
        while line and len(line)>1:
            if re.match(r"%s"%station.upper(), line):
                type2_records.append( line );
            line = fin.readline()
        return type2_records

def format_deg(ddeg, lat=True):
    ddeg = float(ddeg)
    dd   = int(ddeg)
    mm   = int((ddeg - dd)*60.0e0)
    ss   = (ddeg - dd - mm/60.0)*3600.0
    if lat:
        return "%+03i%02i%05.2f"%(dd,mm,ss)
    else:
        return "%+04i%02i%05.2f"%(dd,mm,ss)

##  Get station info from procsta database

"""
      station_info, must have the following fields:
      [0]  station_id (long int)
      [1]  station_name_DSO (4-char)
      [2]  station_name_OFF (4-char), i.e. official name
      [3]  station_name (long name/location), useful for URANUS network
      [4]  server_name (string)
      [5]  server_protocol (char), e.g. ftp, http, ssh
      [6]  server_domain
      [7]  path_to_30sec_rnx
      [8]  path_to_01sec_rnx
      [9]  username
      [10] password
      [11] network
      [12] datastart
      [13] datastop
      [14-16] x, y, z
      [17-19] lon, lat, hgt
"""

today   = datetime.datetime.now()
dbInfo  = get_db_info(station)
staInfo = get_sta_info(station, sta52f)
rnx_d   = {}
if rinex is not None: rnx_d = get_rnx_info(station,rinex)

warnings=[]
print "#! /bin/bash"
print "sed -e \"s|Date Prepared            : (CCYY-MM-DD)|Date Prepared            : %s|g\" \\"%(today.strftime("%Y-%m-%d"))
print "-e \"s|Report Type              : (NEW/UPDATE)|Report Type              : NEW|g\" \\"
print "-e \"s|Site Name                : |Site Name                : %s|g\" \\"%station.upper()
print "-e \"s|Four Character ID        : (A4)|Four Character ID        : %s|g\" \\"%station.upper()
print "-e \"s|Date Installed           : (CCYY-MM-DDThh:mmZ)|Date Installed           : %s|g\" \\"%(dbInfo[12].strftime("%Y-%m-%d")+"T00:00Z")
print "-e \"s|Country                  : |Country                  : Greece|g\" \\"
print "-e \"s|Tectonic Plate           : |Tectonic Plate           : Eurasian|g\" \\"
print "-e \"s|X coordinate (m)       : |X coordinate (m)       : %s|g\" \\"%(dbInfo[14])
print "-e \"s|Y coordinate (m)       : |Y coordinate (m)       : %s|g\" \\"%(dbInfo[15])
print "-e \"s|Z coordinate (m)       : |Z coordinate (m)       : %s|g\" \\"%(dbInfo[16])
print "-e \"s|Latitude (N is +)      : (+/-DDMMSS.SS)|Latitude (N is +)      : %s|g\" \\"%(format_deg(dbInfo[18], True))
print "-e \"s|Longitude (E is +)     : (+/-DDDMMSS.SS)|Longitude (E is +)     : %s|g\" \\"%(format_deg(dbInfo[17], False))
print "-e \"s|Elevation (m,ellips.)  : (F7.1)|Elevation (m,ellips.)  : %7.1f|g\" \\"%(float(dbInfo[19]))

if "rec_type" in rnx_d:
    rec_type = rnx_d["rec_type"]
    if rec_type != staInfo[0][69:90].strip():
        warnings.append("Rinex Receiver type does not with the one from sta file \""+rec_type+"\" vs \""+staInfo[0][69:90].strip()+"\"")
print "-e \"s|3.1  Receiver Type            : (A20, from rcvr_ant.tab; see instructions)|3.1  Receiver Type            : %20s|g\" \\"%(staInfo[0][69:90])

rec_nr = staInfo[0][91:112]
if "rec_number" in rnx_d:
    rec_number = rnx_d["rec_number"]
    if rec_nr.strip() == "":
        warnings.append("The sta file did not have the receiver number; extracted from RINEX \""+rec_number+"\"")
        rec_nr = rec_number
    if rec_number != rec_nr.strip():
        warnings.append("Rinex Receiver number does not with the one from sta file \""+rec_number+"\" vs \""+rec_nr.strip()+"\"")
print "-e \"s|Serial Number            : (A20, but note the first A5 is used in SINEX)|Serial Number            : %20s|g\" \\"%(rec_nr)

rec_fw = ""
if "rec_firmw" in rnx_d:
    if rnx_d["rec_firmw"].strip() == "":
        rec_fw = rnx_d["rec_firmw"]
        warnings.append("The sta file did not have the receiver firmware; extracted from RINEX: \""+rec_fw+"\"")
print "-e \"s|Firmware Version         : (A11)|Firmware Version         : %11s|g\" \\"%(rec_fw)

if "ant_type" in rnx_d:
    ant_type = rnx_d["ant_type"]
    if ant_type != staInfo[0][121:141].strip():
        warnings.append("Rinex Antenna type does not with the one from sta file \""+ant_type+"\" vs \""+staInfo[0][121:141].strip()+"\"")
print "-e \"s|4.1  Antenna Type             : (A20, from rcvr_ant.tab; see instructions)|4.1  Antenna Type             : %s|g\" \\"%(staInfo[0][121:141])

ant_nr = staInfo[0][141:163]
if "ant_number" in rnx_d:
    ant_number = rnx_d["ant_number"]
    if ant_nr.strip() == "" and ant_number.strip() != "":
        warnings.append("The sta file did not have the antenna number; extracted from RINEX: \""+ant_number+"\".")
        ant_nr = ant_number
    if ant_number != ant_nr.strip():
        warnings.append("Rinex Antenna number does not with the one from sta file \""+ant_number+"\" vs \""+ant_nr.strip()+"\"")
print "-e \"s|Serial Number            : (A*, but note the first A5 is used in SINEX)|Serial Number            : %s|g\" \\"%(ant_nr)

print "-e \"s|Marker->ARP Up Ecc. (m)  : (F8.4)|Marker->ARP Up Ecc. (m)  : %8.4f|g\" \\"%(float(staInfo[0][193:201]))
print "-e \"s|Marker->ARP North Ecc(m) : (F8.4)|Marker->ARP North Ecc(m) : %8.4f|g\" \\"%(float(staInfo[0][173:181]))
print "-e \"s|Marker->ARP East Ecc(m)  : (F8.4)|Marker->ARP East Ecc(m)  : %8.4f|g\" \\"%(float(staInfo[0][183:191]))
print "-e \"s|Antenna Radome Type      : (A4 from rcvr_ant.tab; see instructions)|Antenna Radome Type      : %4s|g\" $1"%(staInfo[0][137:141])
print "sed -n -e '/^%s\s*$/,/^[A-Z]/ p' antenna.gra | sed -e '1d;$d'"%(staInfo[0][121:137].strip())

if len(warnings) :
    print "## ----------- WARNINGS ---------------"
    for i in warnings: print "##",i
    print "## ------------------------------------"
