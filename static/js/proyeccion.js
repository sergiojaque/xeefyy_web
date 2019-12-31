$(document).ready(function () {
$('.porcentaje_estado_resultado').on('focusout', function(e){
                e.preventDefault()
                e.stopPropagation()
                cuenta = this.parentElement.parentElement.children[0].innerText;
                valor = this.value
                entidad = $("#porcentaje_estado_resultado").attr("value")

                console.log(e.currentTarget.value)
                $.ajax({
                    url: '/porcentaje_estado_resultado'+'/'+cuenta+'/'+ valor+'/'+entidad,
                    success: function (respuesta) {
                        console.log(respuesta)
                    },
                    error: function () {
                    }
                })
            })
        });