$(document).ready(function () {
$('.porcentaje_ratios').on('focusout', function(e){
                e.preventDefault()
                e.stopPropagation()
                cuenta = this.parentElement.parentElement.children[0].innerText;
                valor = this.value
                entidad = $("#porcentaje_ratios").attr("value")

                console.log(e.currentTarget.value)
                $.ajax({
                    url: '/porcentaje_ratios'+'/'+cuenta+'/'+ valor+'/'+entidad,
                    success: function (respuesta) {
                        console.log(respuesta)
                    },
                    error: function () {
                    }
                })
            })
        });