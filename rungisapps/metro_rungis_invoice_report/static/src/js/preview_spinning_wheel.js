odoo.define('metro_rungis_invoice_report.preview_spinning_wheel', function (require) {

    $(function(){
       $('#invoice_html').load(function(){
           $('.o_portal_html_loader').hide();
       });
    });

})