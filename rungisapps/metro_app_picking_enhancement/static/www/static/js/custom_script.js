window.onerror = function(msg){
    var scope = angular.element(document.getElementById('mobileAppPicking')).scope();
    scope.showAlertFunc("ERROR: " + msg);
}

function checkScannedBarcode(barcode) {
    document.getElementById('inputBarcode').blur();
    
    var scope = angular.element(document.getElementById('mobileAppPicking')).scope();
        
    if(barcode.includes("O-BTN") || barcode.includes("O-CMD")) {
        
        var sp = barcode.slice(0,6);
        var actionClass = barcode.split(sp);
        
        var ele = document.getElementsByClassName(actionClass[1]);
        if(ele.length > 0) {
            scope.showAlertFunc('');
            var btnAction = ele[0];                
            btnAction.click();
        } else {
            if(actionClass[1] == 'PREV'){
                window.history.back();
            } else if(actionClass[1] == 'NEXT'){
                window.history.forward();
            } else if(actionClass[1] == 'DISCARD'){
                scope.redirectToPickingType();
            } else if(actionClass[1] == 'print-slip'){
                // scope.click_print_delivery_slip();
            } else if(actionClass[1] == 'print-op'){
                scope.click_print_operation();
            }
        }
    } else {
        if(barcode){              
            scope.customScanCall(barcode);
        }
    }
}

function initOnScan(){
            
    var suffixKeyCodes = [9,13];
    var prefixKeyCodes = [];
                            
    var options = {
        timeBeforeScanTest: 100, 
        avgTimeByChar: 30,
        minLength: 2, 
        // suffixKeyCodes: suffixKeyCodes,
        // prefixKeyCodes: prefixKeyCodes, 
        scanButtonLongPressTime: 500, 
        stopPropagation: false, 
        preventDefault: false,
        reactToPaste: true,
        reactToKeyDown: true,
        singleScanQty: 1
    }
    
    options.onScan = function(barcode, qty){
        checkScannedBarcode(barcode);
    };	
    
    try {
        onScan.attachTo(document, options);
    } catch(e) {
        onScan.setOptions(document, options);
    }
}

function checkScannedInput(){
    var inputBarcode = document.getElementById('inputBarcode');
    var inputArray = [];
    inputBarcode.addEventListener('input', function (evt) {
        var scope = angular.element(document.getElementById('mobileAppPicking')).scope();
        scope.showSpinner = true;
        inputArray.push(evt.data);
        if(inputArray.length > 0){
            var barcode = inputArray.join('');
            evt.srcElement.value = '';
            inputArray = [];
            checkScannedBarcode(barcode);
        }
    });
}
    
(function(){
    // initOnScan();

    checkScannedInput();

    document.addEventListener('keydown', function() {
        // need to make sure no other input's are effected
        if (document.activeElement.tagName != 'INPUT') {
            document.getElementById('inputBarcode').focus();
        }
    });
    
})();
