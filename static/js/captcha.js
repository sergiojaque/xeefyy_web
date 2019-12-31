function Captcha(mainCaptcha, inputName) {
    var alpha1 = new Array('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '!', '@', '# ', ',', '.', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+', '[', ']', '{', '}', '"', ':', ';', '/', '?', '<', '>', '|');
    var alpha2 = new Array('!', '@', '# ', ',', '.', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+', '[', ']', '{', '}', '"', ':', ';', '/', '?', '<', '>', '|');
    var alpha3 = new Array('1', '2', '3', '4', '5', '6', '7', '8', '9', '0');
    var i;
    for (i = 0; i < 6; i++) {
        var a = alpha1[Math.floor(Math.random() * alpha1.length)];
        var b = alpha2[Math.floor(Math.random() * alpha2.length)];
        var c = alpha3[Math.floor(Math.random() * alpha3.length)];
        var d = alpha1[Math.floor(Math.random() * alpha1.length)];
        var e = alpha2[Math.floor(Math.random() * alpha2.length)];
        var f = alpha3[Math.floor(Math.random() * alpha3.length)];
        var g = alpha1[Math.floor(Math.random() * alpha1.length)];
    }
    var code = a + ' ' + b + ' ' + c + ' ' + d + ' ' + e + ' ' + f + ' ' + g;
    createCookie('c', code, 0.0025); //solo 3 minutos de cookie
    //crear el captcha en el div seleccionado
    var contenedor = document.getElementById(mainCaptcha);
    contenedor.innerHTML = '';
    //primera columna
    var div = document.createElement('div');
    div.className = "col-lg-6 col-md-6 col-sm-6 col-xs-6";
    //columna para la imagen
    var div1 = document.createElement('div');
    div1.className = "col-lg-10 col-md-10 col-sm-10 col-xs-10";
    var captcha = document.createElement('canvas');
    captcha.id = 'captcha';
    div1.appendChild(captcha);
    div.appendChild(div1);
    //columna para el refresh
    div1 = document.createElement('div');
    div1.className = "col-lg-2 col-md-2 col-sm-2 col-xs-2";
    var refresh = document.createElement('a');
    refresh.id = "refresh";
    refresh.innerHTML = '';
    refresh.href = "javascript:void(0);";
    refresh.setAttribute('onclick', "Captcha('" + mainCaptcha + "');");
    div1.appendChild(refresh);
    div.appendChild(div1);
    contenedor.appendChild(div);
    //columna para el texto
    div = document.createElement('div');
    div.className = "col-lg-6 col-md-6 col-sm-6 col-xs-6";
    div1 = document.createElement('div');
    div1.className = "form-horizontal";
    var input = document.createElement('input');
    input.id = inputName;
    input.className = "form-control";
    div1.appendChild(input);
    div.appendChild(div1);
    contenedor.appendChild(div);
    //columna para el boton
    /*
    div = document.createElement('div');
    div.className = "col-lg-4 col-md-4 col-sm-6 col-xs-12";
    var check = document.createElement('input');
    check.id = "check";
    check.value = "Check";
    check.className = "btn btn-default pull-right";
    check.setAttribute('onclick', "alert(ValidCaptcha('" + mainCaptcha + "', 'txtInput'));");
    div.appendChild(check);
    contenedor.appendChild(div);*/
    CreaIMG(code);
}

function ValidCaptcha(mainCaptcha, inputName) {
    var string1 = removeSpaces(readCookie('c'));
    var string2 = removeSpaces(getElementValue(inputName));
    if (string1 == string2) {
        return true;
    }
    else {
        Captcha(mainCaptcha, inputName);
        return false;
    }
}

function removeSpaces(string) {
    return string.split(' ').join('');
}

function CreaIMG(texto) {
    var ctxCanvas = document.getElementById('captcha').getContext('2d');
    var fontSize = "30px";
    var fontFamily = "Arial";
    var width = 250;
    var height = 50;
    //tamaño
    ctxCanvas.canvas.width = width;
    ctxCanvas.canvas.height = height;
    //color de fondo
    ctxCanvas.fillStyle = "whitesmoke";
    ctxCanvas.fillRect(0, 0, width, height);
    //puntos de distorsion
    ctxCanvas.setLineDash([7, 10]);
    ctxCanvas.lineDashOffset = 5;
    ctxCanvas.beginPath();
    var line;
    for (var i = 0; i < (width); i++) {
        line = i * 5;
        ctxCanvas.moveTo(line, 0);
        ctxCanvas.lineTo(0, line);
    }
    ctxCanvas.stroke();
    //formato texto
    ctxCanvas.direction = 'ltr';
    ctxCanvas.font = fontSize + " " + fontFamily;
    //texto posicion
    var x = (width / 9);
    var y = (height / 3) * 2;
    //color del borde del texto
    ctxCanvas.strokeStyle = "yellow";
    ctxCanvas.strokeText(texto, x, y);
    //color del texto
    ctxCanvas.fillStyle = "red";
    ctxCanvas.fillText(texto, x, y);
}
