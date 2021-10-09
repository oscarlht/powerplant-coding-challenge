function deleteNote(noteId) {
    fetch("/delete-note", {
    method: "POST",
    body: JSON.stringify({ noteId: noteId }),
  }).then((_res) => {
    window.location.href = "/";
  });
}

function myFunction(id, inp) {
    document.getElementById(id).innerHTML = inp;
}

function myFunction2(id, inp) {
    document.getElementById(id).innerHTML = inp;
}