import pandas as pd, numpy as np, json, sys
sys.path.insert(0,'.'); from stem_port import stem
res={}
for tag,prof,data in [('Corning_actual_c1','q2/bout/Corning_mock_actual_c1_profiletable.txt','q2/Corning_mock_actual.txt'),
                      ('MS_actual_c1','q2/bout/MorganStanley_mock_actual_c1_profiletable.txt','q2/MorganStanley_mock_actual.txt'),
                      ('Corning_shuffled_c1','q2/bout/Corning_mock_shuffled_c1_profiletable.txt','q2/Corning_mock_shuffled.txt')]:
    p=pd.read_csv(prof,sep='\t'); P=np.array([[float(x) for x in s.split(',')] for s in p['Profile Model']])
    X=pd.read_csv(data,sep='\t').set_index('Gene Symbol').values
    r=stem(X,P)
    jsig=(p['Cluster (-1 non-significant)']!=-1).values
    res[tag]={'max_abs_count_diff':float(np.abs(r['count']-p['# Genes Assigned'].values).max()),
              'max_abs_expected_diff':float(np.abs(r['expected']-p['# Gene Expected'].values).max()),
              'max_rel_p_diff_sig':float(np.nanmax(np.abs(np.log10(r['p'][jsig])-np.log10(p['p-value'].values[jsig])))) if jsig.any() else None,
              'sig_agree':bool((r['sig']==jsig).all()),'n_sig_port':int(r['sig'].sum()),'n_sig_jar':int(jsig.sum())}
print(json.dumps(res,indent=1)); json.dump(res,open('parity_port_vs_jar.json','w'),indent=1)
