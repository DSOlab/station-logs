#! /usr/bin/python

import datetime
import sys

station = sys.argv[1]

def pretty_print_rec_block(rec_dict, index):
    ''' Print a receiver Information block for a igs log file
    '''
    print '3.{0:1d}  Receiver Type            : {1:20s}'.format(index, rec_dict['Receiver Type'])
    print '     Satellite System         : (GPS+GLO+GAL+BDS+QZSS+SBAS)'
    print '     Serial Number            : {0:20s}'.format(rec_dict['Serial Number'])
    print '     Firmware Version         : {0:11s}'.format(rec_dict['Firmware Version'])
    print '     Elevation Cutoff Setting : (deg)'
    print '     Date Installed           : {0:<21s}'.format(rec_dict['Date Installed'])
    print '     Date Removed             : {0:<21s}'.format(rec_dict['Date Removed'])
    print '     Temperature Stabiliz.    : (none or tolerance in degrees C)'
    print '     Additional Information   : (multiple lines)'
    return

def pretty_print_ant_block(ant_dict, index):
    ''' Print a antenna Information block for a igs log file
    '''
    print '4.{0:1d}  Antenna Type             : {1:20s}'.format(index, ant_dict['Antenna Type'])
    print '     Serial Number            : {0:20s}'.format(ant_dict['Serial Number'])
    print '     Antenna Reference Point  : {0:<21s}'.format(ant_dict['Antenna Reference Point'])
    print '     Marker->ARP Up Ecc. (m)  : {0:8.4f}'.format(ant_dict['Marker Up'])
    print '     Marker->ARP North Ecc(m) : {0:8.4f}'.format(ant_dict['Marker North'])
    print '     Marker->ARP East Ecc(m)  : {0:8.4f}'.format(ant_dict['Marker East'])
    print '     Alignment from True N    : {0:20s}'.format(ant_dict['Alignment from True N'])
    print '     Antenna Radome Type      : {0:4s}'.format(ant_dict['Antenna Radome Type'])
    print '     Radome Serial Number     : {0:10s}'.format(ant_dict['Radome Serial Number'])
    print '     Antenna Cable Type       : {0:20s}'.format(ant_dict['Antenna Cable Type'])
    print '     Antenna Cable Length     : {0:10s}'.format(ant_dict['Antenna Cable Length'])
    print '     Date Installed           : {0:<21s}'.format(ant_dict['Date Installed'])
    print '     Date Removed             : {0:<21s}'.format(ant_dict['Date Removed'])
    print '     Additional Information   : (multiple lines)'
    return

def set_stop_date(dic, epoch):
    ''' Set the last date in a Receiver/Antenna dictionary
    '''
    dic["Date Removed"] = epoch.strftime('%Y-%m-%d')+'T00:00Z' if epoch is not datetime.datetime.max else '(CCYY-MM-DDThh:mmZ)'

def igs_log_ant_inf_block(ant_tp,ant_sn,dnorth,deast,dup,dt_start,dt_stop):
    ''' Compile Antenna information in an igs-log-sheet=like dictionary
    '''
    stop = dt_stop.strftime('%Y-%m-%d')+'T00:00Z' if dt_stop is not datetime.datetime.max else '(CCYY-MM-DDThh:mmZ)'
    return {'Antenna Type': ant_tp,
            'Serial Number': ant_sn,
            'Antenna Reference Point': '(BPA/BCR/XXX from \"antenna.gra\"; see instr.)',
            'Marker Up': dup,
            'Marker North': dnorth,
            'Marker East': deast,
            'Alignment from True N': '(deg; + is clockwise/east)',
            'Antenna Radome Type': ant_tp[-4:],
            'Radome Serial Number': '',
            'Antenna Cable Type': '(vendor & type number)',
            'Antenna Cable Length': '(m)',
            'Date Installed':dt_start.strftime('%Y-%m-%d')+'T00:00Z',
            'Date Removed': stop,
            'Additional Information':''
            }

def igs_log_rec_inf_block(rec_tp,rec_sn,rec_sw,dt_start,dt_stop):
    ''' Compile Receiver information in an igs-log-sheet=like dictionary
    '''
    stop = dt_stop.strftime('%Y-%m-%d')+'T00:00Z' if dt_stop is not datetime.datetime.max else '(CCYY-MM-DDThh:mmZ)'
    return {'Receiver Type': rec_tp,
            'Satellite System': 'GPS+GLO+GAL+BDS+QZSS+SBAS)',
            'Serial Number': rec_sn,
            'Firmware Version': rec_sw,
            'Elevation Cutoff Setting': '',
            'Date Installed':dt_start.strftime('%Y-%m-%d')+'T00:00Z',
            'Date Removed': stop,
            'Temperature Stabiliz.':'',
            'Additional Information':''
            }

with open('station.info', 'r') as fin:
    ##  Initial receiver reference info; if changed, then compile and print a
    ##+ new receiver block.
    rec_tp = ''
    rec_sn = ''
    rec_sw = ''
    prev_rec_stop = datetime.datetime.min
    ##  As above for antenna
    ant_tp = ''
    ant_sn = ''
    prev_ant_stop = datetime.datetime.min
    rec_blocks = [] ## list of receiver blocks
    ant_blocks = [] ## list of antenna blocks
    for line in fin.readlines():
        if station.upper() == line[1:5].upper():
            ## Resolve a GAMIT station.info line to fields
            status       = 0
            station_id   = line[0:7].strip()
            full_name    = line[7:25].strip()
            sess_start   = line[25:44].strip()
            sess_stop    = line[44:63].strip()
            ant_hgt      = float(line[63:72])
            ant_htcod    = line[72:79]
            ant_north    = float(line[79:88])
            ant_east     = float(line[88:97])
            receiver_tp  = line[97:119].strip()
            receiver_vr  = line[119:141].strip()
            sw_vers      = line[141:148].strip()
            receiver_sn  = line[148:170].strip()
            antenna_tp   = "{0:<16s}{1:>4s}".format(line[170:187].strip(),line[187:194].strip())
            antenna_sn   = line[194:].strip()
            ## Resolve the starting date
            try:
            	sess_start   = datetime.datetime.strptime(sess_start, '%Y %j %H %M %S')
            except:
                if sess_start.split()[0] == '9999':
                    sess_start = datetime.datetime.min
                else:
                    print >> sys.stderr, '[ERROR] Invalid datetime: \'%s\''%(sess_start)
                    status = 1
            ## Resolve the ending date
            try:
                sess_stop   = datetime.datetime.strptime(sess_stop, '%Y %j %H %M %S')
            except:
                if sess_stop.split()[0] == '9999':
                    sess_stop = datetime.datetime.max
                else:
                    print >> sys.stderr, '[ERROR] Invalid datetime: \'%s\''%(sess_stop)
                    status = 1
            if status != 0:
                print >> sys.stderr, '       Record not transformed:'
                print >> sys.stderr, '       ['+line.rstrip()+']'
                sys.exit(1)
            ## Check for equipment change
            if receiver_tp != rec_tp or receiver_sn != rec_sn or receiver_vr != rec_sw:
                rec_tp = receiver_tp
                rec_sn = receiver_sn
                rec_sw = receiver_vr
                rec_blocks.append(igs_log_rec_inf_block(rec_tp,rec_sn,rec_sw,sess_start,sess_stop))
            ## If no equipment change, update the last entrie's ending date
            else:
                set_stop_date(rec_blocks[len(rec_blocks)-1], sess_stop)
            if antenna_tp != ant_tp or antenna_sn != ant_sn: ##and antenna_sn != '' and ant_sn != ''
                ant_tp = antenna_tp
                ant_sn = antenna_sn
                ant_blocks.append(igs_log_ant_inf_block(ant_tp,ant_sn,ant_north,ant_east,ant_hgt,sess_start,sess_stop))
            else:
                set_stop_date(ant_blocks[len(ant_blocks)-1], sess_stop)

index = len(rec_blocks)
for i in reversed(rec_blocks):
    print ''
    pretty_print_rec_block(i, index)
    index-=1

index = len(ant_blocks)
for i in reversed(ant_blocks):
    print ''
    pretty_print_ant_block(i, index)
    index-=1
