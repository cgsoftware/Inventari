# -*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import decimal_precision as dp
import time
import netsvc
import pooler, tools
import math
from tools.translate import _

from osv import fields, osv

class inventari(osv.osv):
          
        def _get_product_available_func(states, what):
            #import pdb;pdb.set_trace()
            def _product_available(self, cr, uid, ids, name, arg, context=None):
                return {}.fromkeys(ids, 0.0)
            return _product_available

        _product_qty_available = _get_product_available_func(('done',), ('in', 'out'))
        _product_virtual_available = _get_product_available_func(('confirmed','waiting','assigned','done'), ('in', 'out'))
        _product_outgoing_qty = _get_product_available_func(('confirmed','waiting','assigned'), ('out',))
        _product_incoming_qty = _get_product_available_func(('confirmed','waiting','assigned'), ('in',))
        
        def _product_price(self, cr, uid, ids, name, arg, context=None):
            res = {}
            if context is None:
                ontext = {}
            quantity = context.get('quantity') or 1.0
            pricelist = context.get('pricelist', False)
            if pricelist:
                for id in ids:
                    try:
                        price = self.pool.get('product.pricelist').price_get(cr,uid,[pricelist], id, quantity, context=context)[pricelist]
                    except:
                        price = 0.0
                    res[id] = price
            for id in ids:
                res.setdefault(id, 0.0)
            return res
    
        def _product_lst_price(self, cr, uid, ids, name, arg, context=None):
            res = {}
            product_uom_obj = self.pool.get('product.uom')
            for id in ids:
                res.setdefault(id, 0.0)
            for product in self.browse(cr, uid, ids, context=context):
                if 'uom' in context:
                    uom = product.uos_id or product.uom_id
                    res[product.id] = product_uom_obj._compute_price(cr, uid,
                    uom.id, product.list_price, context['uom'])
                else:
                    res[product.id] = product.list_price
                    res[product.id] =  (res[product.id] or 0.0) * (product.price_margin or 1.0) + product.price_extra
            return res
        
    
        _name = "inventari.temp"
        _description = 'Stampa temporanea Inventario'
        _columns = {
                    'name':fields.char('Articolo', size=64, required=False, readonly=False),
                    'default_code':fields.char('Codice', size=25, required=False, readonly=False),
                    'product_uom': fields.char('Unità di misura', size=15, readonly=False),
                    'qty_available': fields.char('Quantità', size=10, required=False, readonly=False),
                    'unit_price': fields.float('Prezzo Unitario', digits=(16,2)),
                    'tot_value': fields.float('Valore di Inventario', digits=(16,2)),
                    'value_type':fields.selection([
                        ('costo_medio','Costo Medio'),
                        ('ultimo','Ultimo Costo'),
                        ('standard','Costo Standard'),
                        ('lifo','L.I.F.O.'), ],  'Valorizzazione'),
                    
                    }
        

        
        def pulisci(self, cr, uid):
            # cancella tutte le righe prima di iniziare a lavorare
            ids = self.search(cr, uid, [])
            if ids:
                ok = self.unlink(cr, uid, ids)
            return True
    
        def crea_temp(self, cr, uid, ids, data, context=None):
            self.pulisci(cr, uid)
                
            prod_obj = self.pool.get('product.product')
            prod_last = self.pool.get('product.price.history')
            filtro = [('qty_available' ,'>', 0)]
            import pdb;pdb.set_trace()
            prod_ids = prod_obj.search(cr, uid, filtro)
            
            #CALCOLO L'INVENTARIO COSTO MEDIO.... (se openerp mette in price la media degli ultimi costi)
            #DA VERIFICARE
            
            # NON FUNZIONA -->   ???  type = self.browse(cr, uid, ids).value_type ???
            # DOVREBBE LEGGERE IL TIPO DI VALORIZZAZIONE SELEZIONATO , GUARDANDO IL DB DA PGADMIN
            # IL CAMPO RISULTA CORRETTAMENTE VALORIZZATO ....
            type = 'ultimo'
            if type == 'costo_medio': 
                if prod_ids:
                    for prod_line in prod_ids:
                        riga  = prod_obj.browse(cr, uid, [prod_line])[0]
                        if riga.qty_available > 0:
                            
                                riga_inv = {
                                            'name': riga.name,
                                            'default_code': riga.default_code,
                                            'product_uom': riga.product_tmpl_id.uom_id.name,
                                            'qty_available': riga.qty_available,
                                            'unit_price':riga.price,
                                            'tot_value': riga.price * riga.qty_available,                        
                                            }
                                id_inv = self.create(cr, uid, riga_inv)
            #CALCOLO L'INVENTARIO AL METODO DELL'ULTIMO COSTO DI ACQUISTO
            if type == 'ultimo':
                if prod_ids:
                    for prod_line in prod_ids:
                        riga  = prod_obj.browse(cr, uid, [prod_line])[0]
                        if riga.qty_available > 0:
                            last = prod_last.browse(cr, uid, [prod_line])[0]
                            if last.list_price: 
                                riga_inv = {
                                        'name': riga.name,
                                        'default_code': riga.default_code,
                                        'product_uom': riga.product_tmpl_id.uom_id.name,
                                        'qty_available': riga.qty_available,
                                        'unit_price':last.list_price,
                                        'tot_value': riga.qty_avilable * last.list_price,                       
                                    }
                            else:
                                warning = {
                                           'title': 'ATTENZIONE !',
                                           'message':'Non è stato possibile applicare il criterio di valorizzazione richiesto. I dati sono visualizzati secondo il metodo del COSTO MEDIO',
                                           }
                                riga_inv = {
                                            'name': riga.name,
                                            'default_code': riga.default_code,
                                            'product_uom': riga.product_tmpl_id.uom_id.name,
                                            'qty_available': riga.qty_available,
                                            'unit_price':riga.price,
                                            'tot_value': riga.price * riga.qty_available,                        
                                            }
                            id_inv = self.create(cr, uid, riga_inv)
            return {'type': 'ir.actions.act_window_close', 'warning': warning}
        
            #CALCOLO L'INVENTARIO AL METODO 
                     
                
inventari()