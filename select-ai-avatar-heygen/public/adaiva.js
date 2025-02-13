document.getElementById('send').addEventListener('click', function() {
  const question = document.getElementById('question').value;

  // Hacer una solicitud al servidor
  fetch(`/adaiava.send?question=${question}`)
  .then(response => response.json())
  .then(data => {
    // Actualiza el valor en el HTML
    document.getElementById('display').style.display = data.display;
    document.getElementById('message').innerText = data.message;
    document.getElementById('taskInput').value = data.result;
    document.getElementById('result').innerText = data.result;

    var disabled = document.getElementById('start').getAttribute('disabled');
    
    if(question !== "") {
      if(data.result !== ""){
        if (disabled == null || disabled == true) {
          document.getElementById('start').click();
          setTimeout(function() {
            document.getElementById('repeat').click();
          }, 3000);
        } else {
          document.getElementById('repeat').click();
        }
      }
    }

  })
  .catch(error => console.error('Error:', error));
});