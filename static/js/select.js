$(document).ready(function () {
    $('#adicionar').click(function () {

        var i = 1; //contador para asignar id al boton que borrara la fila
        var fila = '<tr id="row' + i + '"><td class="codigo_banco" >' + $("#banco").val() + '</td><td>' + $('select[name="banco"] option:selected').text() + '</td>' +
            '<td><button type="button" name="remove" id="remove_banco" class="btn btn-danger">Quitar</button></td></tr>'; //esto seria lo que contendria la fila

        i++;

        $('#mytable tbody').append(fila);
        $("#adicionados").text(""); //esta instruccion limpia el div adicioandos para que no se vayan acumulando
        var nFilas = $("#mytable tr").length;
        $("#adicionados").append(nFilas - 1);
        //le resto 1 para no contar la fila del header
        document.getElementById("banco").value = "";
        document.getElementById("banco").focus();
        $(".codigo_banco").each(function (index) {
            console.log($(this))
        });

    });
    $(document).on('click', '#remove_banco', function () {
        $(this)[0].parentNode.parentNode.remove()
    });

    $('#adicionarclasificacion').click(function () {

        var i = 1; //contador para asignar id al boton que borrara la fila
        var fila = '<tr id="row' + i + '"><td>' + $("#clasificacion").val() + '</td><td>' + $('select[name="clasificacion"] option:selected').text() + '</td><td>' +
            '<button type="button" name="remove" id="remove_clasificacion" class="btn btn-danger btn_remove">Quitar</button></td></tr>'; //esto seria lo que contendria la fila

        i++;

        $('#mytableclasificacion tbody').append(fila);
        $("#adicionadosclasificacion").text(""); //esta instruccion limpia el div adicioandos para que no se vayan acumulando
        var nFilas = $("#mytableclasificacion tr").length;
        $("#adicionadosclasificacion").append(nFilas - 1);
        //le resto 1 para no contar la fila del header
        document.getElementById("clasificacion").value = "";
        document.getElementById("clasificacion").focus();
        $(".codigo_clasificacion").each(function (index) {
            console.log($(this))
        });

    });
    $(document).on('click', '#remove_clasificacion', function () {
        $(this)[0].parentNode.parentNode.remove()
    });
    $("#update_empresa").change(function () {
        $('#empresa1').children().remove();
        $.ajax({
            url: '/tipoEmpresa' + "/" + $("#update_empresa").val(),
            success: function (respuesta) {
                $("#empresa1").append('<option value="sopciom">seleccione opción...</option>');
                for (let i in respuesta) {

                    $("#empresa1").append('<option value="' + respuesta[i].cod_tipo_entidad + '">' + respuesta[i].desc_tipo_entidad + '</option>');

                }

            },
            error: function () {
            }
        });
    });
    $("#region").change(function () {
        $('#provincia').children().remove();
        $.ajax({
            url: '/regiones' + "/" + $("#region").val(),
            success: function (respuesta) {
                $("#provincia").append('<option value="sopciom">seleccione opción...</option>');
                for (let i in respuesta) {

                    $("#provincia").append('<option value="' + respuesta[i].provincia_id + '">' + respuesta[i].provincia_nombre + '</option>');

                }

            },
            error: function () {
            }
        });
    });
    $("#provincia").change(function () {
        $('#comuna').children().remove();
        $.ajax({
            url: '/provincias' + "/" + $("#provincia").val(),
            success: function (respuesta) {
                $("#comuna").append('<option value="sopciom">seleccione opción...</option>');
                for (let i in respuesta) {

                    $("#comuna").append('<option value="' + respuesta[i].comuna_id + '">' + respuesta[i].comuna_nombre + '</option>');

                }

            },
            error: function () {
            }
        });
    });
    $("#nivel1").change(function () {
        $('#nivel2').children().remove();
        $.ajax({
            url: '/niveles' + "/" + $("#nivel1").val()+"/2" ,
            success: function (respuesta) {
                $("#nivel2").append('<option value="sopciom">seleccione opción...</option>');
                for (let i in respuesta) {

                    $("#nivel2").append('<option value="' + respuesta[i].sector + '">' + respuesta[i].desc_actividad_entidad + '</option>');

                }

            },
            error: function () {
            }
        });
    });
     $("#nivel2").change(function () {
        $('#nivel3').children().remove();
        $.ajax({
            url: '/niveles' + "/" + $("#nivel2").val()+"/3",
            success: function (respuesta) {
                $("#nivel3").append('<option value="sopciom">seleccione opción...</option>');
                for (let i in respuesta) {

                    $("#nivel3").append('<option value="' + respuesta[i].sector + '">' + respuesta[i].desc_actividad_entidad + '</option>');

                }

            },
            error: function () {
            }
        });
    });
      $("#nivel3").change(function () {
        $('#nivel4').children().remove();
        $.ajax({
            url: '/niveles' + "/" + $("#nivel3").val()+"/4",
            success: function (respuesta) {
                $("#nivel4").append('<option value="sopciom">seleccione opción...</option>');
                for (let i in respuesta) {

                    $("#nivel4").append('<option value="' + respuesta[i].sector + '">' + respuesta[i].desc_actividad_entidad + '</option>');

                }

            },
            error: function () {
            }
        });
    });
    $("#btn_acutalizar").click(function () {
        var valores_banco = '';
        $("#mytable").children("tbody").children("tr").each(function () {
            valores_banco += $(this).children()[0].innerText + ",";
        });
        var valores_clasificacion = '';
        $("#mytableclasificacion").children("tbody").children("tr").each(function () {
            valores_clasificacion += $(this).children()[0].innerText + ",";
        });
        console.log(valores_banco);
        console.log(valores_clasificacion);

        $.ajax({
            type: "post",
            data: $("#frm_formulario").serialize() + "&banco=[" + valores_banco + "]" + "&clasificacion=[" + valores_clasificacion + "]",
            url: '/formulario',
            success: function (respuesta) {
                console.log(respuesta)
                if (respuesta == 'error rut no valido') {
                    $('#contenedorFormulario').append('<div class="notification is-danger"><i class="fas fa-award"></i>' + respuesta + '</div>')
                    swal({
                        title: 'ERROR!',
                        text: 'ERROR AL CREA O MODIFICAR LA EMPRESA.',
                        timer: 1000
                    }).then(
                        function () {
                        },
                        // handling the promise rejection
                        function (dismiss) {
                            if (dismiss === 'timer') {
                                console.log('La alerta fue cerrada en 2 segundos')
                                //Aqui puedes hacer tu redireccion
                                history.go(0)

                            }
                        }
                    )

                } else {
                    swal({
                        title: 'CREACION DE EMPRESA!',
                        text: 'EMPRESA CREADA CORRECTAMENTE.',
                        timer: 1000
                    }).then(
                        function () {
                        },
                        // handling the promise rejection
                        function (dismiss) {
                            if (dismiss === 'timer') {
                                console.log('creacion de empresa correcta')
                                //Aqui puedes hacer tu redireccion
                                location.href = "/docEmpresa";
                            }
                        }
                    )
                }
            },
            error: function () {
                console.log("valores_clasificacion");
            }
        });

    });
});


