from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class inherit_res_lang(osv.osv):
    
    '''Herencia del modelo res.lang para cargar por defecto la configuracion del lenguaje es_VE '''
    
    _inherit = 'res.lang'
    
    def load_lang(self, cr, uid, lang, lang_name = None):
        lang_id = super(inherit_res_lang, self).load_lang(cr, uid, lang, lang_name)
        value = self.read(cr, uid, [lang_id], ['code'])
        if value[0].get('code','') == 'es_VE':
            self.write(cr, uid, [lang_id], {'grouping': '[3,3,3,3,3,-1]'})
        return lang_id
    
inherit_res_lang()
