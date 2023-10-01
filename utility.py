import pandas as pd 

gp = pd.read_csv("gp.csv")
addr = pd.read_csv("addr.csv")
gp = gp.drop(gp.columns[0],axis=1)
addr = addr.drop(addr.columns[0],axis=1)

def get_gp():
    return gp

def get_addr():
    return addr

def get_GP_name(CR):
    f = gp.loc[gp.id==CR,:]
    if(len(f)==0):
        return ""
    return f.iloc[0,1]

def get_GP_code(last,first):

    x = gp.loc[gp.name.str.contains(last.upper())]
    if(len(x)==0):
        return '';
    x = x.loc[x.name.str.contains(first.upper())]
    if(len(x)==0):
        return ''
    return x.iloc[0,0]


def get_GP_address(CR):
    i = addr.iloc[addr.loc[addr.userId==CR,:].index,1]
    return i.values[0]

def get_group(CR):
    ind = get_GP_address(CR)
    listaGP = addr.loc[addr.address==ind,'userId']
    nomi = []
    for e in range(0,len(listaGP)):
        nomi.append(get_GP_name(listaGP.values[e]))
    return nomi    
    
