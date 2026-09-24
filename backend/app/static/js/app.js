document.addEventListener("DOMContentLoaded", function () {
    const list = document.getElementById("steps-list");
    if (!list) return;

    const demarcheId = list.dataset.demarcheId;

    list.querySelectorAll(".step-checkbox").forEach((checkbox) => {
        checkbox.addEventListener("change", async (event) => {
            const index = parseInt(event.target.dataset.index, 10);
            const label = event.target.nextElementSibling;

            try {
                const response = await fetch(`/demarches/${demarcheId}/step`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ index }),
                });
                if (!response.ok) throw new Error("request failed");
                const data = await response.json();
                const done = data.steps[index].done;
                event.target.checked = done;
                label.classList.toggle("line-through", done);
                label.classList.toggle("text-slate-400", done);
            } catch (err) {
                event.target.checked = !event.target.checked;
                alert("Impossible de mettre à jour l'étape, réessayez.");
            }
        });
    });
});
