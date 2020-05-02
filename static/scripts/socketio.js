document.addEventListener('DOMContentLoaded',() => {
  var socket = io.connect("https://" + document.domain +":" +location.port);
   socket.on("connect",() => {
     socket.send("Connected");

   }) ;

   socket.on('message',data => {
     cosole.log('message recieved : ${data}');

   });

});
