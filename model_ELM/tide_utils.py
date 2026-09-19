import csv
import os
import subprocess

#Utilities for processing NOAA tidal harmonic constituent files for marsh simulations.
#Amplitude (m) -> mm, Speed (deg/hour) -> period (seconds), Phase (deg) -> radians.

def process_tide_components(tide_components_file, param_file_path, tide_baseline=800.0):
    if not os.path.exists(tide_components_file):
        raise FileNotFoundError('Tide components file not found: '+tide_components_file)
    if not os.path.exists(param_file_path):
        raise FileNotFoundError('Parameter file not found: '+param_file_path)

    required_cols = ['Amplitude','Speed','Phase']
    components = []
    with open(tide_components_file, 'r') as f:
        reader = csv.DictReader(f)
        for col in required_cols:
            if col not in reader.fieldnames:
                raise ValueError('Tide file must contain columns: '+str(required_cols))
        for row in reader:
            components.append(row)

    print('Processing '+str(len(components))+' tide components...')
    for i, comp in enumerate(components):
        amp_mm = float(comp['Amplitude'])*1000.0
        period_sec = 360.0*3600.0/float(comp['Speed'])
        phase_rad = float(comp['Phase'])*3.14159265359/180.0

        cmd = "ncap2 -O -s 'tide_coeff_amp_"+str(i+1)+" = humhol_ht*0+"+format(amp_mm,'.6e')+"' " \
                +param_file_path+' '+param_file_path
        subprocess.run(cmd, shell=True, check=True)
        cmd = "ncap2 -O -s 'tide_coeff_period_"+str(i+1)+" = humhol_ht*0+"+format(period_sec,'.6e')+"' " \
                +param_file_path+' '+param_file_path
        subprocess.run(cmd, shell=True, check=True)
        cmd = "ncap2 -O -s 'tide_coeff_phase_"+str(i+1)+" = humhol_ht*0+"+format(phase_rad,'.6e')+"' " \
                +param_file_path+' '+param_file_path
        subprocess.run(cmd, shell=True, check=True)

    cmd = "ncap2 -O -s 'tide_baseline = humhol_ht*0+"+format(tide_baseline,'.6e')+"' " \
            +param_file_path+' '+param_file_path
    subprocess.run(cmd, shell=True, check=True)
    print('Tide components written to '+param_file_path)
