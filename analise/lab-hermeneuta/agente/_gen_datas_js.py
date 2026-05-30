import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dados/_data_inicio_real_63.json', 'r', encoding='utf-8') as f:
    d = json.load(f)
datas = d['result']['datas']
out = []
for x in datas:
    oid = x['obra_id']
    dt = x.get('data_1a_aplicacao_original')
    cf = x.get('confianca', 'nao_encontrado')
    fn = x.get('fonte', 'nao_encontrado')
    ev_raw = (x.get('evidencia_curta', '') or '').strip()[:300]
    ev = ev_raw.replace(chr(92), '').replace('"', "'")
    dt_str = '"' + dt + '"' if dt else 'null'
    out.append('    "' + oid + '": {d:' + dt_str + ',c:"' + cf + '",f:"' + fn + '",e:"' + ev + '"},')
with open('dados/_datas_js.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print(f'Saved {len(out)} entries')
