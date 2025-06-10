document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("search-input");
  const cards = Array.from(document.querySelectorAll("#cards-container .card"));
  const checkboxes = Array.from(document.querySelectorAll(".filters input[type='checkbox']"));

  // ───── FUNC: Filtro principal ─────
  function filtrar() {
    const texto = searchInput.value.trim().toLowerCase();
    const disciplinasAtivas = checkboxes
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    cards.forEach(card => {
      const name = card.getAttribute("data-name");
      const disc = card.getAttribute("data-discipline");
      const coincideTexto = name.includes(texto);
      const coincideDisc = disciplinasAtivas.includes(disc);

      card.style.display = (coincideTexto && coincideDisc) ? "block" : "none";
    });
  }

  // ───── Eventos para busca e filtros ─────
  searchInput.addEventListener("input", filtrar);
  checkboxes.forEach(cb => cb.addEventListener("change", filtrar));

  // ───── Atalho clicando na tag da disciplina ─────
  document.querySelectorAll(".discipline-label").forEach(label => {
    label.addEventListener("click", function () {
      const disciplina = this.textContent.trim();
      checkboxes.forEach(cb => {
        cb.checked = (cb.value === disciplina);
      });
      searchInput.value = "";
      filtrar();
    });
  });

  // ───── Notyf para notificação bonita ─────
  const notyf = new Notyf({
    duration: 2500,
    ripple: true,
    position: { x: 'right', y: 'bottom' }
  });

  // ───── Função de cópia com notify ─────
  window.copyLink = function (url) {
    navigator.clipboard.writeText(url)
      .then(() => {
        notyf.success('🔗 Enlace copiado al portapapeles');
      })
      .catch(err => {
        console.error('Error al copiar enlace:', err);
        notyf.error('❌ No se pudo copiar el enlace');
      });
  };

  filtrar(); // filtro inicial
});
