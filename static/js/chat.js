var ws;
var username;
function onKeyUp(event)
{
    if (event.keyCode == 13)
        sendMessage();
}
function sendMessage()
{
    message = document.getElementById("message");
    if (message.value)
    {
        ws.send("<strong>" + username + "</strong>: " + message.value);
        message.value = "";
    }
    message.focus();
}
function checkSupport()
{
    if (!("WebSocket" in window))
    {
        document.getElementById("login").innerHTML = "Este navegador no soporta WebSockets.";
    }
}
function loadChat()
{
    username = document.getElementById("username").value;
    if (!username)
        return;
    document.getElementById("login").hidden = true;
    document.getElementById("chat").hidden = false;
    messages = document.getElementById("messages");
    messages.innerHTML = "";
    ws = new WebSocket("ws://localhost:9998");
    ws.onopen = function()
    {
        ws.send(username + " ha ingresado al chat.");
    };
    ws.onclose = function()
    {
        chat.innerHTML = "Se ha perdido la conexión."
    };
    ws.onmessage = function(evt)
    {
        messages.innerHTML += evt.data + "<br />";
        messages.scrollTop = messages.scrollHeight;
    };
}
function closeChat()
{
    ws.send(username + " se ha desconectado.");
    ws.close();
}