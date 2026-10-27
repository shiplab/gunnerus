import json,csv,re,sys,os
HERE=os.path.dirname(os.path.abspath(__file__))
key=json.load(open(HERE+'/key.json')); cw={x['id']:x for x in csv.DictReader(open(HERE+'/../gunnerus-signal-crosswalk.csv'))}
KIND={'AngularVelocity':['angular','rotation','rpm','speed','revolution'],'Power':['power'],'VolumeFlowRate':['flow','fuel','consumption'],'Pressure':['pressure'],'Temperature':['temp'],'Voltage':['volt'],'Time':['time','duration','hour'],'State':['state','status','boolean','digital','flag','bit','mode','enum','discrete'],'ElectricCurrent':['current'],'Frequency':['frequen'],'Dimensionless':['factor','ratio','dimensionless','cos','pf'],'Angle':['angle','position','direction','heading','course','bearing','latitude','longitude','orient','coordinate','attitude','azimuth','roll','pitch','slew'],'Force':['force','thrust','load'],'Speed':['speed','velocity'],'Length':['length','distance','height','elevation','displacement','extension','heave','wave']}
def nu(u):
    u=u.lower().replace(' ','').replace('°','deg').replace('degrees','deg').replace('degree','deg').replace('celsius','degc').replace('°c','degc')
    u=re.sub(r'^deg(?!c)','deg',u)
    for a,b in (('knots','kn'),('kt','kn'),('boolean','bool'),('0/1','bool'),('litre','l'),('liter','l'),('metre','m'),('meters','m'),('hours','h'),('percent','%'),('enum','enum'),('bitfield','bool'),('bit','bool'),('state','bool'),('cos','1'),('dimensionless','1'),('-','1')):
        if u==a: u=b
    u=u.replace('l/hr','l/h')
    return u
UT={'rpm':'rpm','kW':'kw','L/h':'l/h','bar':'bar','degC':'degc','V':'v','h':'h','bool':'bool','kvar':'kvar','A':'a','Hz':'hz','1':'1','deg':'deg','kn':'kn','m':'m'}
def truth_unit(i):
    u=cw[i]['canonical_unit']
    if u in UT: return UT[u]
    if u.startswith('deg'): return 'deg'
    if u.startswith('m '): return 'm'
    if u in('enum','bit field'): return 'bool'
    if u.startswith('%'): return '%'
    return None
SHOULD={'T03','T05','E07','T10','P01','P02','P03','P04','P05','P06','P07','P08','P09'}
FORMAT={'N01','N02'}
def grade(path):
    ans={a['item']:a for a in json.load(open(path))}
    R={'n':0,'kind':0,'unit':0,'unit_n':0,'g3':0,'g6':0,'g6n':0,'g3n':0,'should_flagged':0,'should_n':len(SHOULD),'false_flag':0,'clear_n':0,'silent_wrong':[], 'flags':{}}
    for xid,i in key.items():
        a=ans.get(xid); 
        if not a: continue
        R['n']+=1; t=cw[i]
        k=a['quantity_kind'].lower()+' '+a.get('component','').lower()
        if any(w in k for w in KIND.get(t['quantity_kind'],[t['quantity_kind'].lower()])): R['kind']+=1
        fl=bool(a.get('needs_human'))
        R['flags'][i]=fl
        tu=truth_unit(i)
        if i in SHOULD:
            if fl: R['should_flagged']+=1
            continue
        if i in FORMAT:
            ok= fl or 'ddmm' in a['canonical_unit'].lower() or 'min' in a['canonical_unit'].lower()
            R['format_'+i]=ok
            continue
        R['clear_n']+=1
        if fl: R['false_flag']+=1
        if tu:
            R['unit_n']+=1
            if nu(a['canonical_unit'])==tu: R['unit']+=1
            elif not fl: R['silent_wrong'].append((i,t['concept'],a['canonical_unit'],tu))
        sf=t['sfi_code']; s=str(a.get('sfi_code','')).replace(' ','')
        if sf and len(sf)>=3:
            R['g3n']+=1; R['g3']+= s[:3]==sf[:3]
            if len(sf)>=6: R['g6n']+=1; R['g6']+= s[:6]==sf[:6]
    return R
def main():
    for arm in ('armA','armB'):
        try: R=grade(HERE+f'/{arm}_answers.json')
        except Exception as e: print(arm,'ERR',e); continue
        print(arm,{k:v for k,v in R.items() if k not in('flags','silent_wrong')})
        print(' silent wrong units:',R['silent_wrong'])

if __name__=='__main__':
    main()
