"""Validación de accounting de arrays; fixtures locales no son jobs reales."""
import re

def validate_accounting(text,job,count):
    if not str(job).isdecimal() or type(count)is not int or count<1:raise ValueError('JobID e índices válidos requeridos')
    rows={}
    for line in text.splitlines():
        if not line.strip():continue
        cols=[x.strip() for x in line.split('|')]
        if len(cols)!=5:raise ValueError('Formato sacct esperado: JobID|State|ExitCode|Elapsed|NodeList')
        match=re.fullmatch(re.escape(str(job))+r'_(\d+)',cols[0])
        if not match:raise ValueError('Accounting no expandido o JobID ajeno')
        i=int(match[1])
        if i in rows:raise ValueError('Índice de accounting duplicado')
        if cols[1]!='COMPLETED' or cols[2]!='0:0' or not cols[4] or cols[4] in {'None','Unknown'}:raise ValueError('Tarea sin finalización/nodo/exit correcto')
        rows[i]=dict(index=i,state=cols[1],exit_code=cols[2],elapsed=cols[3],nodes=cols[4])
    if set(rows)!=set(range(count)):raise ValueError('Accounting vacío o incompleto; no verificar HPC')
    return [rows[i] for i in range(count)]
