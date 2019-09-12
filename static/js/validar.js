function validar(){
    var username,password;
    username= document.getElementById("username").value;
    password= document.getElementById("password").value;

    if(username ==="" ){
        alert("El campo Username está vacio ");
        return false;
    }
    else if(password ===""){
        alert("El campo Password está vacio");

    }
    if(username.length>30 || password.length>15){
        alert("El nombre o contraseña son muy largos");
        return false;
    }
}