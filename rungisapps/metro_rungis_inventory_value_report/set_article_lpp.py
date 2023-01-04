url = 'http://0.0.0.0:8015'
db = 'metro_pp'
username = 'mehjabin.farsana@metro.digital'
password = '1'
import xmlrpc.client
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
common.version()
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
product_ids = models.execute_kw(db, uid, password,'product.product', 'search',[[['purchase_ok', '=', True]]])
for product in product_ids:
	models.execute_kw(db, uid, password,'product.product', 'set_product_last_purchase',[[product], {}])