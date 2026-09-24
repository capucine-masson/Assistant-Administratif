document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("chatbot-toggle");
    const closeBtn = document.getElementById("chatbot-close");
    const panel = document.getElementById("chatbot-panel");
    const form = document.getElementById("chatbot-form");
    const input = document.getElementById("chatbot-input");
    const messages = document.getElementById("chatbot-messages");

    if (!toggle || !panel || !form) return;

    function openPanel() {
        panel.classList.remove("translate-x-full");
        toggle.classList.remove("chatbot-pulse");
        input.focus();
    }
    function closePanel() {
        panel.classList.add("translate-x-full");
    }

    toggle.addEventListener("click", openPanel);
    closeBtn.addEventListener("click", closePanel);

    function addBubble(text, who) {
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble chat-bubble-${who}`;
        bubble.textContent = text;
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;
        return bubble;
    }

    function addTaskCard(demarche) {
        const card = document.createElement("a");
        card.href = demarche.url;
        card.className = "chat-bubble chat-bubble-bot block hover:border-primary/40";
        card.innerHTML = `
            <div class="flex items-center gap-2 text-primary font-medium">
                <i data-lucide="circle-check-big" class="w-4 h-4"></i>
                <span>${demarche.title}</span>
            </div>
            <div class="text-xs text-slate-400 mt-1">Voir la démarche →</div>
        `;
        messages.appendChild(card);
        messages.scrollTop = messages.scrollHeight;
        if (window.lucide) lucide.createIcons();
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = input.value.trim();
        if (!message) return;

        addBubble(message, "user");
        input.value = "";

        const loading = document.createElement("div");
        loading.className = "chat-bubble-loading";
        loading.innerHTML = "<span></span><span></span><span></span>";
        messages.appendChild(loading);
        messages.scrollTop = messages.scrollHeight;

        try {
            const response = await fetch("/chatbot/message", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message }),
            });
            const data = await response.json();
            loading.remove();

            addBubble(data.reply, "bot");
            if (data.demarche) {
                addTaskCard(data.demarche);
            }
        } catch (err) {
            loading.remove();
            addBubble("Désolé, une erreur est survenue. Réessayez.", "bot");
        }
    });
});
