import os
import csv
import xmlrpclib
import re


HOST='localhost'
PORT=28069
DB='produccion-06'
USER='admin'
PASS='12345'
url ='http://%s:%d/xmlrpc/' % (HOST,PORT)

common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')
uid = common_proxy.login(DB,USER,PASS)

def html_escape(text):
    """Produce entities within text.""" 
    html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }
    return "".join(html_escape_table.get(c,c) for c in text)
     
def _compare(estado):
     if estado is True:
        path_file_open = '../data/EEA.csv'
        path_file_madi = '../data/MadiEEA.csv'
        archive_open = csv.DictReader(open(path_file_open))
        archive_madi = csv.DictReader(open(path_file_madi))
        dic_open = {}
        dic_madi = {}
        cont = 0
        for field_open in archive_open:
            depre = html_escape(field_open["DEPRE"].replace('"', '').replace("'", '').strip())
            code = html_escape(field_open["CODE"].replace('"', '').replace("'", '').strip())
            dic_open.update({code:depre})
            
        for field_madi in archive_madi:
            depre = html_escape(field_madi["DEPREMES"].replace('"', '').replace("'", '').strip())
            code = html_escape(field_madi["CODIGO"].replace('"', '').replace("'", '').strip())
            code = str(code).zfill(6)
            dic_madi.update({code:depre})

        for key in dic_open.keys():
            if not key in dic_madi.keys():
                print key
                cont = cont + 1
        print 'cantidad: ',cont
        #~ print 'OPEN: ',dic_open
        #~ print 'MADI: ',dic_madi



def _generate(estado):
    if estado is True:
        path_file = '../data/activos.csv'
        archive = csv.DictReader(open(path_file))
        shops = { 
        'H':'BARCELONA',
        'D':'MARGARITA',
        'M':'MATURIN',
        'C':'CUMANA',
        'U':'ZULIA',
        'Z':'ZULIA',
        'O':'ORDAZ',
        'B':'ORDAZ',
        'G':'BOLIVAR',
        'K':'CARUPANO',
        'P':'FALCON',
        'F':'FALCON',
        'A':'SEDE',#sede principal
        'X':'SEDE',#sede principal
        'T':'SEDE',#sede principal
        }  
        cont = 1
        for field in archive:
            sucu = html_escape(field["COD_SUC"].replace('"', '').replace("'", '').strip())
            code = html_escape(field["CODIGO"].replace('"', '').replace("'", '').strip())
            codigo = str(code).zfill(6)
            ccat = html_escape(field["COD_CAT"].replace('"', '').replace("'", '').strip())
            codcat = ccat[2:3]
            EMO = codcat and codcat or 'A'
           
            sucursal = object_proxy.execute(DB,uid,PASS,'sale.shop','search',[('name','like','%'+shops[EMO]+'%')])
            sucursal = sucursal and sucursal[0] 
            

            if sucu == '0' or sucu == '1' or sucu == '10' or sucu == '11' or sucu == '13' or EMO == 'A' or EMO == 'X' or EMO == 'T':
                
                codigo = str(code).zfill(6)
                asset_id = object_proxy.execute(DB,uid,PASS,'account.asset.asset','search',[('code','=',codigo)])
                print 'codigo: ',codigo
                print 'asset_id: ',asset_id
                if asset_id:
                    registro = object_proxy.execute(DB,uid,PASS,'account.asset.asset', 'write', asset_id, {'shop_id': sucursal })
                    print 'Se actualizo el registro numero: ',cont
                    cont = cont + 1
def __main__():
    print 'Ha comenzado la actualizacion'
    _generate(False)
    _compare(True)
    print 'Ha finalizado la actualizacion de la tabla'
__main__()
