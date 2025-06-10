document.addEventListener("DOMContentLoaded", function() {
  const searchInput = document.getElementById("search-input");
  const cbMat = document.getElementById("filter-matematica");
  const cbCien = document.getElementById("filter-ciencias");
  const cards = Array.from(document.querySelectorAll("#cards-container .card"));

  function filtrar() {
    const texto = searchInput.value.trim().toLowerCase();
    const okMath = cbMat.checked;
    const okCien = cbCien.checked;

    cards.forEach(card => {
      const name = card.getAttribute("data-name");
      const disc = card.getAttribute("data-discipline");
      const coincideTexto = name.includes(texto);
      const coincideDisc =
        (disc === "Matemática" && okMath) || (disc === "Ciencias" && okCien);

      card.style.display = (coincideTexto && coincideDisc) ? "block" : "none";
    });
  }

  searchInput.addEventListener("input", filtrar);
  cbMat.addEventListener("change", filtrar);
  cbCien.addEventListener("change", filtrar);

  document.querySelectorAll(".discipline-label").forEach(label => {
    label.addEventListener("click", function() {
      const disciplina = this.textContent.trim();
      cbMat.checked = (disciplina === "Matemática");
      cbCien.checked = (disciplina === "Ciencias");
      searchInput.value = "";
      filtrar();
    });
  });

function copyLink(url) {
  navigator.clipboard.writeText(url)
    .then(() => {
      // Notificación sencilla; puedes mejorar con un tooltip o toast
      alert('Enlace copiado al portapapeles:\n' + url);
    })
    .catch(err => {
      console.error('Error al copiar enlace:', err);
      alert('No se pudo copiar el enlace');
    });
}


  filtrar();
});

